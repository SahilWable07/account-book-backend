from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from uuid import UUID as UUID_t , UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.transaction import Transaction
from app.models.ledger import Ledger
from app.models.bank_account import BankAccount
from app.schemas.transaction import TransactionAutoCreate
from app.schemas.transaction import TransactionUpdate
from app.utils.financial_settings import FinancialSettingsService
from app.utils.transaction_limits import enforce_daily_limit


class TransactionService:
    """
    Service responsible for transaction lifecycle and balance adjustments.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_gst_ledger(self, *, client_id: UUID_t, user_id: UUID_t, tx_type: str) -> Ledger | None:
        """
        Returns the GST ledger based on transaction type.
        - For expense/loan_receivable: GST Paid (input credit)
        - For income/loan_payable: GST Collected (output tax)
        """
        if tx_type in ["expense", "loan_receivable"]:
            name = "GST Paid"
            ledger_type = "expense"
        elif tx_type in ["income", "loan_payable"]:
            name = "GST Collected"
            ledger_type = "income"
        else:
            return None

        ledger = (
            self.db.query(Ledger)
            .filter(
                Ledger.client_id == client_id,
                Ledger.user_id == user_id,
                Ledger.name.ilike(name),
            )
            .first()
        )
        if ledger is None:
            ledger = Ledger(
                client_id=client_id,
                user_id=user_id,
                name=name,
                type=ledger_type,
                balance=Decimal("0.0"),
            )
            self.db.add(ledger)
            self.db.flush()
        return ledger

    def _resolve_or_create_ledger(self, *, client_id: UUID_t, user_id: UUID_t, tx_type: str) -> Ledger:
        type_to_default_name = {
            "income": "Income",
            "expense": "Expense",
            "loan_payable": "Loan Payable",
            "loan_receivable": "Loan Receivable",
        }
        default_name = type_to_default_name.get(tx_type, tx_type.title())
        ledger = self.db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.user_id == user_id,
            Ledger.name.ilike(default_name)
        ).first()
        if ledger is None:
            ledger = Ledger(
                client_id=client_id,
                user_id=user_id,
                name=default_name,
                type=tx_type,
                balance=Decimal("0.0"),
            )
            self.db.add(ledger)
            self.db.flush()
        return ledger

    def create_with_auto_ledger(self, payload: TransactionAutoCreate) -> Transaction:
        # Enforce per-user daily transaction cap
        enforce_daily_limit(
            self.db,
            user_id=payload.user_id,
            client_id=payload.client_id,
        )

        settings = FinancialSettingsService(self.db).get_active_settings(
            user_id=str(payload.user_id), client_id=str(payload.client_id)
        )
        gst_rate = None
        if settings and settings.gst_enabled and payload.include_gst:
            gst_rate = Decimal(str(settings.gst_rate))
        bank_account = self.db.query(BankAccount).filter(
            BankAccount.id == payload.bank_account_id,
            BankAccount.client_id == payload.client_id,
            BankAccount.user_id == payload.user_id,
        ).first()
        if bank_account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")

        ledger = self._resolve_or_create_ledger(
            client_id=payload.client_id,
            user_id=payload.user_id,
            tx_type=payload.type,
        )

        amount = Decimal(str(payload.amount))
        base_amount = None
        gst_amount = None
        if gst_rate is not None and gst_rate > 0:
            divisor = Decimal("1") + (gst_rate / Decimal("100"))
            base_amount = (amount / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            gst_amount = (amount - base_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Adjust balances: bank always by total amount; ledgers split into base and GST when applicable
        if payload.type in ["expense", "loan_receivable"]:
            if bank_account.balance < amount:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")
            bank_account.balance -= amount
            if gst_amount and gst_amount > 0:
                ledger.balance += base_amount or Decimal("0.00")
                gst_ledger = self._get_gst_ledger(client_id=payload.client_id, user_id=payload.user_id, tx_type=payload.type)
                if gst_ledger:
                    gst_ledger.balance += gst_amount
            else:
                ledger.balance += amount
        elif payload.type in ["income", "loan_payable"]:
            bank_account.balance += amount
            if gst_amount and gst_amount > 0:
                ledger.balance += base_amount or Decimal("0.00")
                gst_ledger = self._get_gst_ledger(client_id=payload.client_id, user_id=payload.user_id, tx_type=payload.type)
                if gst_ledger:
                    gst_ledger.balance += gst_amount
            else:
                ledger.balance += amount
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported transaction type")

        tx = Transaction(
            client_id=payload.client_id,
            user_id=payload.user_id,
            ledger_id=ledger.id,
            bank_account_id=bank_account.id,
            type=payload.type,
            amount=amount,
            base_amount=base_amount,
            gst_amount=gst_amount,
            description=payload.description,
        )

        self.db.add(tx)
        try:
            self.db.commit()
            self.db.refresh(tx)
            return tx
        except Exception:
            self.db.rollback()
            raise

    def _reverse_effects_for_transaction(self, tx: Transaction):
        bank_account = self.db.query(BankAccount).filter(BankAccount.id == tx.bank_account_id).first()
        ledger = self.db.query(Ledger).filter(Ledger.id == tx.ledger_id).first()
        if bank_account is None or ledger is None:
            return
        amount = Decimal(str(tx.amount))
        gst_part = Decimal(str(tx.gst_amount)) if tx.gst_amount is not None else Decimal("0.00")
        base_part = (
            Decimal(str(tx.base_amount)) if tx.base_amount is not None else (amount - gst_part)
        )

        # Reverse bank movement
        if tx.type in ["expense", "loan_receivable"]:
            bank_account.balance += amount
            # Reverse main ledger (only base)
            ledger.balance -= base_part
            # Reverse GST ledger if present
            if gst_part > 0:
                gst_ledger = self._get_gst_ledger(client_id=tx.client_id, user_id=tx.user_id, tx_type=tx.type)
                if gst_ledger:
                    gst_ledger.balance -= gst_part
        elif tx.type in ["income", "loan_payable"]:
            bank_account.balance -= amount
            ledger.balance -= base_part
            if gst_part > 0:
                gst_ledger = self._get_gst_ledger(client_id=tx.client_id, user_id=tx.user_id, tx_type=tx.type)
                if gst_ledger:
                    gst_ledger.balance -= gst_part

    def update(self, *, transaction_id: UUID, user_id: UUID, client_id: UUID, payload: TransactionUpdate) -> Transaction:
        tx = (
            self.db.query(Transaction)
            .filter(
                Transaction.id == transaction_id,
                Transaction.client_id == client_id,
                Transaction.user_id == user_id,
                Transaction.is_deleted == False,
            )
            .first()
        )
        if tx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found for this user/group",
            )

        self._reverse_effects_for_transaction(tx)

        # Resolve target bank account (fallback to existing)
        if payload.bank_account_id:
            new_bank = (
                self.db.query(BankAccount)
                .filter(
                    BankAccount.id == payload.bank_account_id,
                    BankAccount.client_id == client_id,
                    BankAccount.user_id == user_id,
                )
                .first()
            )
            if new_bank is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found"
                )
        else:
            new_bank = (
                self.db.query(BankAccount)
                .filter(BankAccount.id == tx.bank_account_id)
                .first()
            )

        # Determine effective type and ledger
        effective_type = payload.type or tx.type
        if payload.type:
            new_ledger = self._resolve_or_create_ledger(
                client_id=client_id, user_id=user_id, tx_type=effective_type
            )
        else:
            new_ledger = (
                self.db.query(Ledger)
                .filter(Ledger.id == tx.ledger_id)
                .first()
            )

        # Determine amount
        amount = Decimal(str(payload.amount)) if payload.amount else Decimal(str(tx.amount))

        # Recompute GST breakdown when requested or when prior tx had GST and amount changed
        settings = FinancialSettingsService(self.db).get_active_settings(
            user_id=str(user_id), client_id=str(client_id)
        )
        base_amount = tx.base_amount
        gst_amount = tx.gst_amount
        recompute_gst = False
        if payload.include_gst is not None:
            recompute_gst = True
        elif tx.gst_amount is not None and payload.amount is not None:
            # amount changed and previous tx had GST
            recompute_gst = True

        if recompute_gst:
            if payload.include_gst and settings and getattr(settings, "gst_enabled", False):
                gst_rate = Decimal(str(getattr(settings, "gst_rate", 0)))
                if gst_rate > 0:
                    divisor = Decimal("1") + (gst_rate / Decimal("100"))
                    base_amount = (amount / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    gst_amount = (amount - base_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    base_amount = None
                    gst_amount = None
            else:
                base_amount = None
                gst_amount = None

        # Apply new effects based on effective type, splitting base and GST where applicable
        gst_part = Decimal(str(gst_amount)) if gst_amount is not None else Decimal("0.00")
        base_part = (
            Decimal(str(base_amount)) if base_amount is not None else (amount - gst_part)
        )

        if effective_type in ["expense", "loan_receivable"]:
            if new_bank.balance < amount:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
                )
            new_bank.balance -= amount
            new_ledger.balance += base_part
            if gst_part > 0:
                gst_ledger = self._get_gst_ledger(client_id=client_id, user_id=user_id, tx_type=effective_type)
                if gst_ledger:
                    gst_ledger.balance += gst_part
        elif effective_type in ["income", "loan_payable"]:
            new_bank.balance += amount
            new_ledger.balance += base_part
            if gst_part > 0:
                gst_ledger = self._get_gst_ledger(client_id=client_id, user_id=user_id, tx_type=effective_type)
                if gst_ledger:
                    gst_ledger.balance += gst_part
        else:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported transaction type"
            )

        # Persist field changes
        if payload.bank_account_id:
            tx.bank_account_id = new_bank.id
        if payload.type:
            tx.ledger_id = new_ledger.id
            tx.type = effective_type
        if payload.amount:
            tx.amount = amount
        if payload.description is not None:
            tx.description = payload.description
        # If GST was recomputed, persist the breakdown
        if recompute_gst:
            tx.base_amount = base_amount
            tx.gst_amount = gst_amount

        try:
            self.db.commit()
            self.db.refresh(tx)
            return tx
        except Exception:
            self.db.rollback()
            raise

    def delete(self, *, tx_id, client_id, user_id) -> None:
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.client_id == client_id,
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
        ).first()
        if tx is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        self._reverse_effects_for_transaction(tx)
        tx.is_deleted = True
        tx.deleted_at = func.now()
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise   
