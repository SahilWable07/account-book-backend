# In app/models/invitation.py

import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    invited_user_id = Column(UUID(as_uuid=True), nullable=False, index=True) 
    invited_by_user_id = Column(UUID(as_uuid=True), nullable=False)

    mobile_number = Column(String(20), nullable=True) 

    status = Column(String(20), nullable=False, default='pending') 
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())