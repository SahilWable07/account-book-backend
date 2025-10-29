from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple 
from app.models.inventory import Inventory
from app.models.transaction import Transaction
from app.models.ledger import Ledger
from app.models.bank_account import BankAccount
from app.schemas.inventory import InventoryCreate
from app.utils.financial_settings import FinancialSettingsService
from app.utils.transaction_limits import enforce_daily_limit


class InventoryService:
    """
    Service encapsulating inventory operations and their financial side-effects.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_item(self, inventory_item: InventoryCreate) -> Tuple[Inventory, Transaction]:
        """
        Creates a new inventory item and a corresponding financial transaction.
        Returns both the created inventory item and the transaction.
        """
        # Enforce per-user daily transaction cap
        enforce_daily_limit(
            self.db,
            user_id=inventory_item.user_id,
            client_id=inventory_item.client_id,
        )
        bank_account = (
            self.db.query(BankAccount)
            .filter(
                BankAccount.id == inventory_item.bank_account_id,
                BankAccount.user_id == inventory_item.user_id,
            )
            .first()
        )
        if not bank_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found for this user.",
            )

        if bank_account.balance < inventory_item.total_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance."
            )

        ledger = (
            self.db.query(Ledger)
            .filter(
                Ledger.client_id == inventory_item.client_id,
                Ledger.user_id == inventory_item.user_id,
                Ledger.name.ilike("Inventory"),
            )
            .first()
        )
        if not ledger:
            ledger = Ledger(
                name="Inventory",
                type="expense",
                client_id=inventory_item.client_id,
                user_id=inventory_item.user_id,
                balance=Decimal("0.0"),
            )
            self.db.add(ledger)
            self.db.flush()

        settings = FinancialSettingsService(self.db).get_active_settings(
            user_id=str(inventory_item.user_id), client_id=str(inventory_item.client_id)
        )
        amount_excl_gst = inventory_item.total_value
        gst_amount = Decimal("0.00")
        if settings and settings.gst_enabled and settings.gst_rate:
            gst_rate = Decimal(str(settings.gst_rate))
            if gst_rate > 0:
                divisor = Decimal("1") + (gst_rate / Decimal("100"))
                amount_excl_gst = (inventory_item.total_value / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                gst_amount = (inventory_item.total_value - amount_excl_gst).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bank_account.balance -= inventory_item.total_value
        ledger.balance += amount_excl_gst
        # Record GST on a separate ledger as input tax credit
        if gst_amount > 0:
            gst_ledger = (
                self.db.query(Ledger)
                .filter(
                    Ledger.client_id == inventory_item.client_id,
                    Ledger.user_id == inventory_item.user_id,
                    Ledger.name.ilike("GST Paid"),
                )
                .first()
            )
            if not gst_ledger:
                gst_ledger = Ledger(
                    name="GST Paid",
                    type="expense",
                    client_id=inventory_item.client_id,
                    user_id=inventory_item.user_id,
                    balance=Decimal("0.0"),
                )
                self.db.add(gst_ledger)
                self.db.flush()
            gst_ledger.balance += gst_amount

        db_item = Inventory(
            client_id=inventory_item.client_id,
            user_id=inventory_item.user_id,
            item_name=inventory_item.item_name,
            description=inventory_item.description,
            category=inventory_item.category,
            quantity=inventory_item.quantity,
            unit_price=inventory_item.unit_price,
            total_value=inventory_item.total_value,
            unit=inventory_item.unit,
        )
        self.db.add(db_item)

        db_transaction = Transaction(
            client_id=inventory_item.client_id,
            user_id=inventory_item.user_id,
            ledger_id=ledger.id,
            bank_account_id=bank_account.id,
            type="expense",
            amount=inventory_item.total_value,
            base_amount=amount_excl_gst, 
            gst_amount=gst_amount,
            description=f"Purchase of {inventory_item.quantity} {inventory_item.item_name}",
        )
        self.db.add(db_transaction)

        try:
            self.db.commit()
            self.db.refresh(db_item)
            self.db.refresh(db_transaction)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database commit failed: {e}",
            )

        return db_item, db_transaction
