
import uuid
from sqlalchemy import Column, String, Numeric, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    item_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    quantity = Column(Numeric(18, 2), default=0.0)
    unit_price = Column(Numeric(18, 2), default=0.0)
    total_value = Column(Numeric(18, 2), default=0.0)
    unit = Column(String(20), nullable=True)
    is_active = Column(String(10), default='active')
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())