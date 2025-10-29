# In app/utils/user_management_service.py

from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User
from app.models.invitation import Invitation
from app.schemas.user_management import UserInviteCreate

class UserManagementService:
    def __init__(self, db: Session):
        self.db = db

    def create_invitation(self, payload: UserInviteCreate) -> Invitation:
        """
        Final code to invite a user with proper validation.
        """
        inviting_user = self.db.query(User).filter(User.user_id == payload.invited_by_user_id).first()

        if not inviting_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The admin user sending the invitation does not exist."
            )

        if inviting_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins are allowed to invite new users."
            )

        if not payload.email and not payload.mobile_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or mobile number is required to invite a user."
            )

        user_to_invite = None
        if payload.email:
            user_to_invite = self.db.query(User).filter(User.email == payload.email).first()
        elif payload.mobile_number:
            user_to_invite = self.db.query(User).filter(User.mobile_number == payload.mobile_number).first()
        
        if not user_to_invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to invite not found with the provided email or mobile number."
            )
        
        if inviting_user.user_id == user_to_invite.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admins cannot invite themselves."
            )
            
        existing_invitation = self.db.query(Invitation).filter(
            and_(
                Invitation.client_id == payload.client_id,
                Invitation.invited_user_id == user_to_invite.user_id,
                Invitation.status == 'pending'
            )
        ).first()

        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user already has a pending invitation for this company."
            )

        # --- NAVIN BADAL ITHE AHE ---
        # Aapan mobile_number la invitation object madhe save karat ahot.
        db_invitation = Invitation(
            client_id=payload.client_id,
            invited_user_id=user_to_invite.user_id,
            invited_by_user_id=payload.invited_by_user_id,
            mobile_number=payload.mobile_number, # <-- Hi line add keli ahe
            status='pending'
        )

        self.db.add(db_invitation)
        self.db.commit()
        self.db.refresh(db_invitation)
        
        return db_invitation