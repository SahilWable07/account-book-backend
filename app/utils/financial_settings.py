
import uuid
from sqlalchemy.orm import Session
from app.models.financial_settings import FinancialSettings
from app.schemas.financial_settings import FinancialSettingsCreate
from fastapi import HTTPException, status
from typing import List

class FinancialSettingsService:
    """
    Service for managing financial settings lifecycle and queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: FinancialSettingsCreate) -> FinancialSettings:
        new_settings = FinancialSettings(**payload.model_dump())
        self.db.add(new_settings)
        self.db.commit()
        self.db.refresh(new_settings)
        return new_settings

    def list_by_user(self, user_id: str, client_id: str, limit: int = 10, offset: int = 0) -> List[FinancialSettings]:
        settings = (
            self.db.query(FinancialSettings)
            .filter(
                FinancialSettings.user_id == user_id,
                FinancialSettings.client_id == client_id
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
        return settings

    def get_active_settings(self, user_id: str, client_id: str) -> FinancialSettings | None:
        return (
            self.db.query(FinancialSettings)
            .filter(
                FinancialSettings.user_id == user_id,
                FinancialSettings.client_id == client_id,
            )
            .order_by(FinancialSettings.financial_year_start.desc())
            .first()
        )