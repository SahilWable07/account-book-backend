# In app/schemas/transaction.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from uuid import UUID
from decimal import Decimal
import datetime



class TransactionAutoCreate(BaseModel):
    client_id: UUID
    user_id: UUID
    bank_account_id: UUID
    type: Literal["income", "expense", "loan_payable", "loan_receivable"]
    amount: Decimal = Field(..., gt=0)
    description: str
    include_gst: Optional[bool] = False

class TransactionUpdate(BaseModel):
    bank_account_id: Optional[UUID] = None
    type: Optional[Literal["income", "expense", "loan_payable", "loan_receivable"]] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    include_gst: Optional[bool] = None

class TransactionFromQueryCreate(BaseModel):
    client_id: UUID
    user_id: UUID
    query: str = Field(..., min_length=5)
    bank_account_id: Optional[UUID] = None

class TransactionOut(BaseModel):
    id: UUID
    ledger_id: UUID
    bank_account_id: UUID
    type: str
    amount: Decimal # Total Amount
    base_amount: Optional[Decimal] = None # Amount without GST
    gst_amount: Optional[Decimal] = None # The GST part
    description: str
    created_at: datetime.datetime
    
    # Pydantic v2 config for ORM parsing
    model_config = ConfigDict(from_attributes=True)
