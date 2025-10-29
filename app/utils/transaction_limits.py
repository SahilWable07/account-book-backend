from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.transaction import Transaction


def enforce_daily_limit(
    db: Session,
    *,
    user_id: UUID,
    client_id: UUID,
    limit: int | None = None,
) -> None:
    """
    Ensures a user cannot create more than `limit` transactions today (server DB date).
    Excludes soft-deleted transactions.
    Raises HTTPException 429 when the limit is reached.
    """
    max_per_day = limit if limit is not None else settings.MAX_TRANSACTIONS_PER_DAY

    todays_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == user_id,
            Transaction.client_id == client_id,
            Transaction.is_deleted == False,
            func.date(Transaction.created_at) == func.current_date(),
        )
        .scalar()
    )

    if todays_count >= max_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily transaction limit reached (max {max_per_day} per day).",
        )

