# In app/models/transaction.py

import uuid
from sqlalchemy import (Column, String, Numeric, Text,
                        ForeignKey, TIMESTAMP, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledgers.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True)

    type = Column(String(30), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)  # This is the TOTAL amount
    base_amount = Column(Numeric(18, 2), nullable=True) # Amount without GST
    gst_amount = Column(Numeric(18, 2), nullable=True) # The GST part

    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    ledger = relationship("Ledger", back_populates="transactions")
    bank_account = relationship("BankAccount", back_populates="transactions")