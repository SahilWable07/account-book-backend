from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.utils.invitation_status import InvitationService

router = APIRouter(prefix="/invitation", tags=["Invitation"])

@router.get("/status")
def get_invitation_status(
    mobile_number: str = Query(..., description="User's mobile number"),
    invitation_id: str = Query(..., description="Unique invitation ID"),
    db: Session = Depends(get_db)
):
    """
    ✅ Check if the user has an accepted or pending invitation.
    - Returns True if accepted, False if pending.
    - If not found, raises 404.
    """
    service = InvitationService(db)
    response = service.get_invitation_status(mobile_number, invitation_id)
    return response
