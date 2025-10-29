# In app/api/v1/endpoints/user_management.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.user_management import UserInviteCreate, UserInviteResponse
from app.utils.user_management_service import UserManagementService

router = APIRouter()

@router.post("/invite", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: UserInviteCreate,
    db: Session = Depends(get_db)
):
    """
    Admin la navin user invite karnyacha endpoint.
    """
    service = UserManagementService(db)
    invitation = service.create_invitation(payload)
    
    response_data = UserInviteResponse.model_validate(invitation, from_attributes=True)

    return ApiResponse(
        success=True,
        status_code=201,
        message="Invitation sent successfully.",
        data=response_data
    )
