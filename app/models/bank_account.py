
import uuid
from sqlalchemy import (Column, String, Numeric, TIMESTAMP, text, 
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False) 
    
    account_name = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=True)
    
    account_type = Column(String(20), nullable=False, default='bank')
    balance = Column(Numeric(18, 2), default=0.0)
    is_active = Column(String(10), default='active')
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), 
                        server_default=func.now(), onupdate=func.now())
    
    transactions = relationship("Transaction", back_populates="bank_account")
    
    __table_args__ = (
        UniqueConstraint('client_id', 'user_id', 'account_name', name='_group_user_account_name_uc'),
    )