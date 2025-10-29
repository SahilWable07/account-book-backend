
# In app/schemas/bank_account.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
import datetime

class BankAccountBase(BaseModel):
    account_name: str = Field(..., max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    account_type: str = Field("bank", max_length=20)
    balance: float = 0.0

class BankAccountCreate(BankAccountBase):
    client_id: UUID
    user_id: UUID 
    token: Optional[str] = None


class BankAccountOut(BankAccountBase):
    id: UUID
    client_id: UUID
    is_active: str
    created_at: datetime.datetime
    
    # Pydantic v2 config for ORM parsing
    model_config = ConfigDict(from_attributes=True)


# --- Schema for Creating a Cash Account ---
class CashAccountCreate(BaseModel):
    client_id: UUID
    user_id: UUID
    balance: float = 0.0
    token: Optional[str] = None
