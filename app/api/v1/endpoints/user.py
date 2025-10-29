
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_management import UserSetup, UserResponse 
from app.utils.user_service import UserService

router = APIRouter()

@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def store_user_endpoint(
    payload: UserSetup,
    db: Session = Depends(get_db)
):
    """
    External user chi mahiti gheun tyala local DB madhe save (store) karto.
    """
    service = UserService(db)
    stored_user = service.setup_account_type(payload=payload)
    return stored_user