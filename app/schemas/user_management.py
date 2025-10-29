from pydantic import BaseModel, EmailStr, UUID4, Field, ConfigDict 
from typing import Literal, Optional
from uuid import UUID


class UserSetup(BaseModel):
    user_id: UUID4 
    client_id: UUID4 
    name: str
    email: EmailStr
    mobile_number: Optional[str] = Field(None, max_length=20) # <-- Add keli line
    account_type: Literal["individual", "company"]


class UserResponse(BaseModel):
    id: str 
    user_id: UUID4
    client_id: UUID4 
    email: EmailStr
    name: str
    mobile_number: Optional[str] # <-- Add keli line
    is_company: bool
    role: str
    
    # Pydantic v2 config for ORM parsing
    model_config = ConfigDict(from_attributes=True)

class UserInviteCreate(BaseModel):
    client_id: UUID  # Company ID
    invited_by_user_id: UUID # Admin chi ID
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

class UserInviteResponse(BaseModel):
    id: UUID
    client_id: UUID
    invited_user_id: UUID
    status: str


    # Pydantic v2 config for ORM parsing
    model_config = ConfigDict(from_attributes=True)
