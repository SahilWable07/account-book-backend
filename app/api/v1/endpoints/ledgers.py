
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ledger as ledger_schema
from app.schemas.common import ApiResponse
from app.utils.ledger_utils import LedgerService

router = APIRouter()

@router.post("/", response_model=ApiResponse, status_code=201)
def create_new_ledger(
    ledger_in: ledger_schema.LedgerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ledger by calling the utility function.
    """
    new_ledger = LedgerService(db).create(ledger_in)
    return ApiResponse(
        success=True,
        status_code=201,
        message="Ledger created successfully",
        data={"id": str(new_ledger.id)}
    )


@router.get("/{client_id}/{user_id}", response_model=ApiResponse)
def read_ledgers_for_group_user(
    client_id: UUID,
    user_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated ledgers for given client_id and user_id.
    """
    rows, total = LedgerService(db).page_by_group_user(client_id=client_id, user_id=user_id, page=page, size=size)

    items = [ledger_schema.LedgerListItem.model_validate(r, from_attributes=True) for r in rows]
    total_pages = (total + size - 1) // size
    data_list = [i.model_dump() for i in items]

    return ApiResponse(
        success=True,
        status_code=200,
        message="Ledgers fetched successfully",
        data=data_list,
        meta={
            "total_items": total,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": size,
        }
    )
