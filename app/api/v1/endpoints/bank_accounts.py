
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.bank_account import BankAccountCreate, BankAccountOut, CashAccountCreate
from app.schemas.common import ApiResponse
from app.utils.bank_accounts import BankAccountService

router = APIRouter()

@router.post("/bank", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    bank_account_in: BankAccountCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new bank or cash account by calling the service layer.
    """
    service = BankAccountService(db)
    new_account = service.create_account(bank_account_in)
        
    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,
        message="Bank account created successfully",
        data=BankAccountOut.model_validate(new_account, from_attributes=True)
    )

@router.post("/cash", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_cash_account(
    cash_in: CashAccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create or return the single cash account by calling the service layer.
    """
    bank_account_in = BankAccountCreate(
        client_id=cash_in.client_id,
        user_id=cash_in.user_id,
        balance=cash_in.balance,
        token=cash_in.token,
        account_type='cash',
        account_name='Cash' 
    )
    
    service = BankAccountService(db)
    cash_account = service.create_account(bank_account_in)

    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,
        message="Cash account created successfully",
        data=BankAccountOut.model_validate(cash_account, from_attributes=True)
    )

@router.get("/{client_id}/{user_id}", response_model=ApiResponse)
def get_user_bank_accounts(client_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve all bank accounts for a specific user by calling the service layer.
    """
    service = BankAccountService(db)
    accounts = service.get_all_by_user(client_id=client_id, user_id=user_id)
    
    return ApiResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Bank accounts fetched successfully",
        data=[BankAccountOut.model_validate(a, from_attributes=True) for a in accounts]
    )
