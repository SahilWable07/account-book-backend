from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

from app.models.transaction import Transaction
from app.models.ledger import Ledger
from app.models.bank_account import BankAccount
from app.schemas.transaction import TransactionFromQueryCreate
from app.schemas.bank_account import BankAccountOut
from app.schemas.inventory import InventoryCreate
from app.services.gemini_services import parse_transaction_query
from app.utils.inventory_utils import InventoryService
from app.utils.financial_settings import FinancialSettingsService
from app.utils.transaction_limits import enforce_daily_limit

class TransactionQueryService:

    def __init__(self, db: Session):
        self.db = db

    def find_or_create_ledger(self, name: str, type: str, client_id: UUID, user_id: UUID) -> Ledger:
        ledger = self.db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.user_id == user_id,
            Ledger.name.ilike(name)
        ).first()
        if not ledger:
            ledger = Ledger(name=name.capitalize(), type=type, client_id=client_id, user_id=user_id, balance=Decimal("0.0"))
            self.db.add(ledger)
            self.db.flush()
        return ledger

    def handle_query_transaction(self, payload: TransactionFromQueryCreate) -> Dict[str, Any] | Transaction:
        if not payload.bank_account_id:
            parsed = parse_transaction_query(payload.query)
            if "error" in parsed:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=parsed)
            
            accounts = self.db.query(BankAccount).filter(BankAccount.client_id == payload.client_id, BankAccount.user_id == payload.user_id).all()
            if not accounts:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bank accounts found.")
            
            if 'total_amount' in parsed:
                parsed['amount'] = parsed.pop('total_amount')

            return {"accounts": [BankAccountOut.model_validate(a, from_attributes=True) for a in accounts], "preview": parsed}
        
        return self.create_from_query(payload)

    def create_from_query(self, payload: TransactionFromQueryCreate) -> Transaction:
        # Enforce per-user daily transaction cap before creating
        enforce_daily_limit(
            self.db,
            user_id=payload.user_id,
            client_id=payload.client_id,
        )

        parsed_data = parse_transaction_query(payload.query)
        
        if "error" in parsed_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse query: {parsed_data.get('error', 'Missing required fields')}")

        # ADDED CHECK: Ensure amount is present and greater than zero
        amount_key = 'total_amount' if 'total_amount' in parsed_data else 'amount'
        if amount_key not in parsed_data or Decimal(str(parsed_data.get(amount_key, 0))) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction amount not specified or is zero. Please provide the transaction amount."
            )
        
        if "error" in parsed_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse query: {parsed_data.get('error', 'Missing required fields')}")

        # === INVENTORY LOGIC (RELIABLE VERSION) ===
        if "inventory" in parsed_data and parsed_data["inventory"]:
            inventory_data = parsed_data["inventory"]
            
            inventory_in = InventoryCreate(
                client_id=payload.client_id,
                user_id=payload.user_id,
                bank_account_id=payload.bank_account_id,
                item_name=inventory_data.get("item", "Unknown Item"),
                quantity=inventory_data.get("quantity", 1),
                unit_price=inventory_data.get("unit_price", 0),
                total_value=inventory_data.get("total_value", 0),
                category=parsed_data.get("category"),
                description=parsed_data.get("description")
            )
            
            inventory_service = InventoryService(self.db)
            
            # InventoryService ata inventory aani transaction donhi return karto.
            new_inventory_item, created_transaction = inventory_service.create_item(inventory_in)
            
            # Direct transaction return kara, shodhaychi (searching) garaj nahi.
            return created_transaction
        
        # === NON-INVENTORY LOGIC ===
        else:
            amount_key = 'total_amount' if 'total_amount' in parsed_data else 'amount'
            if amount_key not in parsed_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse query: {parsed_data.get('error', 'Missing required fields')}")

            bank_account = self.db.query(BankAccount).filter(BankAccount.id == payload.bank_account_id, BankAccount.user_id == payload.user_id).first()
            if not bank_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found.")

            total_amount = Decimal(str(parsed_data[amount_key]))
            gst_details = parsed_data.get("gst_details")
            
            base_amount = total_amount
            gst_amount = Decimal("0.0")
            
            if gst_details:
                base_amount = Decimal(str(gst_details.get("base_amount", total_amount))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                gst_amount = Decimal(str(gst_details.get("gst_amount", "0.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                if gst_amount > 0:
                    # Choose correct GST ledger based on type
                    if parsed_data["type"] in ["income", "loan_payable"]:
                        gst_ledger = self.find_or_create_ledger("GST Collected", "income", payload.client_id, payload.user_id)
                    else:
                        gst_ledger = self.find_or_create_ledger("GST Paid", "expense", payload.client_id, payload.user_id)
                    gst_ledger.balance += gst_amount
            else:
                # Fallback GST calculation using active financial settings
                settings = FinancialSettingsService(self.db).get_active_settings(
                    user_id=str(payload.user_id), client_id=str(payload.client_id)
                )
                if settings and getattr(settings, "gst_enabled", False):
                    try:
                        gst_rate = Decimal(str(getattr(settings, "gst_rate", 0)))
                    except Exception:
                        gst_rate = Decimal("0")
                    if gst_rate > 0 and parsed_data.get("type") in ["income", "expense"]:
                        divisor = Decimal("1") + (gst_rate / Decimal("100"))
                        base_amount = (total_amount / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        gst_amount = (total_amount - base_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        # Post GST to appropriate ledger
                        if gst_amount > 0:
                            if parsed_data["type"] == "income":
                                gst_ledger = self.find_or_create_ledger("GST Collected", "income", payload.client_id, payload.user_id)
                            else:
                                gst_ledger = self.find_or_create_ledger("GST Paid", "expense", payload.client_id, payload.user_id)
                            gst_ledger.balance += gst_amount

            main_ledger = self.find_or_create_ledger(name=parsed_data["category"], type=parsed_data["type"], client_id=payload.client_id, user_id=payload.user_id)
          
            if parsed_data["type"] in ["expense", "loan_receivable"]:
                if bank_account.balance < total_amount:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance.")
                bank_account.balance -= total_amount
            elif parsed_data["type"] in ["income", "loan_payable"]:
                bank_account.balance += total_amount
            
            main_ledger.balance += base_amount

            db_transaction = Transaction(
                client_id=payload.client_id, user_id=payload.user_id,
                ledger_id=main_ledger.id, bank_account_id=bank_account.id,
                type=parsed_data["type"], amount=total_amount,
                base_amount=base_amount, gst_amount=gst_amount,
                description=parsed_data["description"]
            )
            self.db.add(db_transaction)

            try:
                self.db.commit()
                self.db.refresh(db_transaction)
            except Exception as e:
                self.db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database commit failed: {e}")
                
            return db_transaction
