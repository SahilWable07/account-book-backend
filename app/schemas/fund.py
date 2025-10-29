# In app/schemas/fund.py

from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class FundTransferCreate(BaseModel):
    """Schema for creating a fund transfer"""
    company_id: UUID = Field(..., description="ID of the company (admin's user_id)")
    user_id: UUID = Field(..., description="ID of the user receiving the funds")
    amount: Decimal = Field(..., gt=0, description="Amount to transfer (must be positive)")
    description: Optional[str] = Field(None, description="Description of the fund transfer")

    class Config:
        from_attributes = True

class FundTransferResponse(BaseModel):
    """Schema for fund transfer response"""
    fund_id: UUID
    company_id: UUID
    user_id: UUID
    amount: Decimal
    description: Optional[str]
    transferred_at: datetime

    class Config:
        from_attributes = True

class FundTransferSuccess(BaseModel):
    """Schema for successful fund transfer response"""
    success: bool = True
    message: str
    transfer_details: FundTransferResponse

    class Config:
        from_attributes = True
