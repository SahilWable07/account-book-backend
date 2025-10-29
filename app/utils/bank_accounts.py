
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Tuple, List, Optional
from uuid import UUID
import logging
import requests

from app.models.bank_account import BankAccount
from app.core.config import settings
from app.schemas.bank_account import BankAccountCreate
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class BankAccountService:
    """
    Service class encapsulating bank account related operations and integrations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_cash_account(self, client_id, user_id, initial_balance: float = 0.0) -> Tuple[BankAccount, bool]:
        """
        Retrieve existing cash account for (client_id, user_id) or create one.
        Returns (account, created_new_flag).
        """
        existing_cash = self.db.query(BankAccount).filter(
            BankAccount.client_id == client_id,
            BankAccount.user_id == user_id,
            BankAccount.account_type == 'cash'
        ).first()

        if existing_cash:
            return existing_cash, False

        new_cash = BankAccount(
            client_id=client_id,
            user_id=user_id,
            account_name="Cash",
            account_type="cash",
            balance=initial_balance,
            is_active='active'
        )

        self.db.add(new_cash)
        try:
            self.db.commit()
            self.db.refresh(new_cash)
            return new_cash, True
        except IntegrityError:
            self.db.rollback()
            existing_cash = self.db.query(BankAccount).filter(
                BankAccount.client_id == client_id,
                BankAccount.user_id == user_id,
                BankAccount.account_type == 'cash'
            ).first()
            if existing_cash:
                return existing_cash, False
            raise

    def verify_remote_user_exists(self, client_id: UUID, user_id: UUID, bearer_token: str) -> bool:
        """
        Call external auth API to verify that the user exists.
        """
        if not bearer_token:
            logger.warning("User verify: missing Authorization header for client_id=%s user_id=%s", client_id, user_id)
            return False

        token = bearer_token.strip().replace("Bearer ", "")
        url = f"{settings.AUTH_API_URL}{client_id}/user/{user_id}"
        headers = {"authorization": f"Bearer {token}"}
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.status_code == 200
        except requests.RequestException as exc:
            logger.error("User verify: request failed: %s", exc)
            return False

    def create_account(self, bank_account_in: BankAccountCreate) -> BankAccount:
        """
        Handles the entire logic for creating a new bank or cash account.
        """
        # 1. User Verification
        if not self.verify_remote_user_exists(
            client_id=bank_account_in.client_id,
            user_id=bank_account_in.user_id,
            bearer_token=bank_account_in.token or ""
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "User verification failed.", "code": "USER_VERIFY_FAILED"}
            )

        # 2. Handle 'cash' account
        if bank_account_in.account_type.lower() == 'cash':
            cash_account, created = self.get_or_create_cash_account(
                client_id=bank_account_in.client_id,
                user_id=bank_account_in.user_id,
                initial_balance=bank_account_in.balance
            )
            if not created:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "CASH_ACCOUNT_EXISTS", "message": "Cash account already exists."}
                )
            return cash_account

        
        payload_dict = bank_account_in.model_dump(exclude={"token"})
        new_account = BankAccount(**payload_dict)
        self.db.add(new_account)
        
        try:
            self.db.commit()
            self.db.refresh(new_account)
            return new_account
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "A bank account with this name already exists.", "code": "BANK_ACCOUNT_DUPLICATE"}
            )

    def get_all_by_user(self, client_id: UUID, user_id: UUID) -> List[BankAccount]:
        """
        Retrieve all bank accounts for a specific user.
        """
        accounts = self.db.query(BankAccount).filter(
            BankAccount.client_id == client_id,
            BankAccount.user_id == user_id
        ).all()
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "No bank accounts found for this user.", "code": "BANK_ACCOUNT_NOT_FOUND"}
            )
        return accounts

