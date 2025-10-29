from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from decimal import Decimal


class InventoryCreate(BaseModel):
    client_id: UUID
    user_id: UUID
    bank_account_id: UUID  # <-- Added this line
    item_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    total_value: Decimal = Field(..., gt=0)
    unit: Optional[str] = Field(None, max_length=20)


class InventoryUpdate(BaseModel):
    item_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    total_value: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=20)


class InventoryOut(BaseModel):
    id: UUID
    client_id: UUID
    user_id: UUID
    item_name: str
    description: Optional[str]
    category: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    total_value: Decimal
    unit: Optional[str]
    
    # Pydantic v2 config for ORM parsing
    model_config = ConfigDict(from_attributes=True)
