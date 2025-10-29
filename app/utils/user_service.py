# In app/utils/user_service.py

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
import uuid 

from app.models.user import User
from app.schemas.user_management import UserSetup 

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def setup_account_type(self, payload: UserSetup) -> User:
        """
        Final code to create a user. Handles duplicates and creates a plain UUID for the primary key.
        """
        # Check for existing user by user_id, email, or mobile number
        existing_user = self.db.query(User).filter(
            or_(
                User.user_id == payload.user_id,
                User.email == payload.email,
                User.mobile_number == payload.mobile_number
            )
        ).first()

        if existing_user:
            if existing_user.user_id == payload.user_id:
                detail = f"User with user_id '{payload.user_id}' already exists."
            elif existing_user.email == payload.email:
                detail = f"User with email '{payload.email}' already exists."
            else:
                detail = f"User with mobile number '{payload.mobile_number}' already exists."
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail
            )

        account_type_cleaned = payload.account_type.lower().strip()
        is_company_flag = (account_type_cleaned == "company")
        user_role = "admin" if is_company_flag else "user"

        # Create a plain UUID string for the 'id' primary key
        new_custom_id = str(uuid.uuid4())

        # Create the new user object
        new_user = User(
            id=new_custom_id, 
            user_id=payload.user_id,
            client_id=payload.client_id, 
            name=payload.name,
            email=payload.email,
            mobile_number=payload.mobile_number,
            is_company=is_company_flag,
            role=user_role
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user