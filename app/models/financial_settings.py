
import uuid
from sqlalchemy import Column, Date, String, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class FinancialSettings(Base):
    __tablename__ = "financial_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    financial_year_start = Column(Date, nullable=False)
    currency_code = Column(String(10), default='INR')
    language = Column(String(20), default='en')
    timezone = Column(String(50), default='Asia/Kolkata')
    
    gst_enabled = Column(Boolean, nullable=False, default=False)
    gst_rate = Column(Numeric(5, 2), nullable=False, default=0.0)  