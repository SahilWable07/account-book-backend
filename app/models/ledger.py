
import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False, index=True) 
    balance = Column(Numeric(18, 2), default=0.0)
    
    
    transactions = relationship("Transaction", back_populates="ledger")