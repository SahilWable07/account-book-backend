# In app/utils/fund_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.fund import Fund
from app.models.user import User
from app.schemas.fund import FundTransferCreate, FundTransferResponse

class FundService:
    def __init__(self, db: Session):
        self.db = db

    def transfer_funds(self, payload: FundTransferCreate) -> FundTransferResponse:
        """
        Transfer funds from company (admin) to user.
        
        Business Rules:
        1. Only users with role = "admin" can send funds
        2. The company_id should be the admin's user_id
        3. The target user must exist and cannot be another admin
        4. Amount must be positive
        """
        
        # 1. Verify that the company_id belongs to an admin
        # Search by both id and user_id to handle different client implementations
        admin_user = self.db.query(User).filter(
            (User.id == str(payload.company_id)) | (User.user_id == payload.company_id)
        ).first()
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {payload.company_id} not found"
            )
        
        if admin_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can transfer funds"
            )
        
        # 2. Verify that the target user exists and is not an admin
        # Search by both id and user_id to handle different client implementations
        target_user = self.db.query(User).filter(
            (User.id == str(payload.user_id)) | (User.user_id == payload.user_id)
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {payload.user_id} not found"
            )
        
        if target_user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer funds to another admin user"
            )
        
        # 3. Validate amount
        if payload.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer amount must be positive"
            )
        
        # 4. Create the fund transfer record
        # Use the actual user_id from the database records
        fund_transfer = Fund(
            company_id=admin_user.user_id,  # Use the actual user_id from the admin record
            user_id=target_user.user_id,    # Use the actual user_id from the target user record
            amount=payload.amount,
            description=payload.description
        )
        
        self.db.add(fund_transfer)
        self.db.commit()
        self.db.refresh(fund_transfer)
        
        # 5. Return the response
        return FundTransferResponse(
            fund_id=fund_transfer.fund_id,
            company_id=fund_transfer.company_id,
            user_id=fund_transfer.user_id,
            amount=fund_transfer.amount,
            description=fund_transfer.description,
            transferred_at=fund_transfer.transferred_at
        )