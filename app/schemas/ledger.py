# In app/schemas/ledger.py

from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import ClassVar
from decimal import Decimal
from uuid import UUID

# Shared properties for a ledger
class LedgerBase(BaseModel):
    name: str = Field(..., max_length=100, examples=["Rent"])
    type: str = Field(..., max_length=20, examples=["expense"])

# Properties to receive via API on creation
class LedgerCreate(LedgerBase):
    client_id: UUID
    user_id: UUID
    balance: Decimal | None = Field(default=None, description="Optional opening balance")

# Properties to return to the client
class LedgerResponse(LedgerBase):
    id: UUID
    client_id: UUID
    balance: Decimal

    # Pydantic v2 configuration to allow ORM object parsing (kept as ClassVar so it never serializes)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)



class LedgerCreateResponse(BaseModel):
    id: UUID
    message: str = "Ledger created successfully"


class LedgerListItem(BaseModel):
    id: UUID
    name: str
    type: str
    balance: Decimal

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)




class Pagination(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    items_per_page: int


class LedgerListResponse(BaseModel):
    data: list[LedgerListItem]
    pagination: Pagination