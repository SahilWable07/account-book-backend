# In app/api/v1/endpoints/funds.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fund import FundTransferCreate, FundTransferResponse, FundTransferSuccess
from app.utils.fund_service import FundService

router = APIRouter()

@router.post("/transfer", response_model=FundTransferSuccess, status_code=status.HTTP_201_CREATED)
def transfer_funds(
    payload: FundTransferCreate,
    db: Session = Depends(get_db)
):
    """
    Transfer funds from company (admin) to user.
    
    Requirements:
    - Only users with role = "admin" can send funds
    - The company_id should be the admin's user_id
    - The target user must exist and cannot be another admin
    - Amount must be positive
    """
    service = FundService(db)
    transfer_result = service.transfer_funds(payload)
    
    return FundTransferSuccess(
        success=True,
        message="Funds transferred successfully",
        transfer_details=transfer_result
    )