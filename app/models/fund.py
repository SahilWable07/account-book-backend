# In app/models/fund.py

import uuid
from sqlalchemy import Column, String, Numeric, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Fund(Base):
    __tablename__ = "funds"

    fund_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    description = Column(Text, nullable=True)
    transferred_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("User", foreign_keys=[company_id], back_populates="funds_sent")
    user = relationship("User", foreign_keys=[user_id], back_populates="funds_received")