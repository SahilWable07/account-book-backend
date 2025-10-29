from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal

class AIInventory(BaseModel):
    item: str
    quantity: Decimal
    unit_price: Decimal
    total_value: Decimal

class AITransaction(BaseModel):
    type: Literal["income", "expense", "loan_payable", "loan_receivable"]
    amount: Decimal
    description: str
    category: str
    inventory: Optional[AIInventory] = None