from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from decimal import Decimal

class FinancialSettingsCreate(BaseModel):
    client_id: UUID
    user_id: UUID
    financial_year_start: date
    currency_code: str = "INR"
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    gst_enabled: bool = False
    gst_rate: Decimal = Decimal("0.00")


class FinancialSettingsResponse(BaseModel):
    id: UUID
    client_id: UUID
    user_id: UUID
    financial_year_start: date
    currency_code: str
    language: str
    timezone: str
    gst_enabled: bool
    gst_rate: Decimal

    model_config = ConfigDict(from_attributes=True)
