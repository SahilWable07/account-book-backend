
from sqlalchemy.orm import Session
from typing import List, Tuple
from uuid import UUID
                          
from app.models.ledger import Ledger
from app.schemas import ledger as ledger_schema

class LedgerService:
    """
    Service for CRUD and querying operations on ledgers.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ledger_schema.LedgerCreate) -> Ledger:
        data = payload.model_dump()
        db_ledger = Ledger(**data)
        self.db.add(db_ledger)
        self.db.commit()
        self.db.refresh(db_ledger)
        return db_ledger

    def page_by_group_user(self, client_id: UUID, user_id: UUID, page: int, size: int) -> Tuple[List[Ledger], int]:
        query = self.db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.user_id == user_id
        )
        total_items = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return items, total_items