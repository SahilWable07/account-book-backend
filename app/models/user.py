import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    client_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile_number = Column(String(20), unique=True, nullable=True, index=True) # <-- Add keli line
    is_company = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default='user', nullable=False)
    is_active = Column(Boolean(), default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    funds_sent = relationship("Fund", foreign_keys="Fund.company_id", back_populates="company")
    funds_received = relationship("Fund", foreign_keys="Fund.user_id", back_populates="user")