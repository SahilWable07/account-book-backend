from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.invitation import Invitation  # your SQLAlchemy model
from uuid import UUID


class InvitationService:
    def __init__(self, db: Session):
        self.db = db

    def get_invitation_status(self, mobile_number: str, invitation_id: str):
        """
        Check invitation status for given mobile number and invitation_id.
        Returns True if accepted, False if pending.
        """

        try:
            inv_id = UUID(invitation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation_id format; must be a UUID",
            )

        invitation = (
            self.db.query(Invitation)
            .filter(
                Invitation.mobile_number == mobile_number,
                Invitation.id == inv_id,
            )
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No invitation found for this user"
            )

        is_accepted = invitation.status.lower() == "accepted"

        return {
            "invitation_id": str(invitation.id),
            "mobile_number": invitation.mobile_number,
            "accepted": is_accepted,
            "message": "Invitation accepted" if is_accepted else "Invitation pending",
        }
