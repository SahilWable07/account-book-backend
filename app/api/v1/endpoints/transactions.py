
from uuid import UUID
from fastapi import APIRouter, Depends, status, Response, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.transaction import TransactionAutoCreate, TransactionFromQueryCreate, TransactionOut, TransactionUpdate
from app.schemas.common import ApiResponse
from app.utils.transaction_query_util import TransactionQueryService
from app.utils.transaction_service import TransactionService

router = APIRouter()

@router.post("/query", response_model=ApiResponse)
def create_transaction_from_natural_language(
    payload: TransactionFromQueryCreate,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Creates a transaction from a query or returns a preview if bank_account_id is missing.
    """
    service = TransactionQueryService(db)
    result = service.handle_query_transaction(payload)

    if isinstance(result, dict):
        response.status_code = status.HTTP_200_OK
        return ApiResponse(
            success=False,
            status_code=status.HTTP_200_OK,
            message="Please select a bank account from the transaction.",
            data=result,
            meta={"requires": "bank_account_id"}
        )

    response.status_code = status.HTTP_201_CREATED
    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,
        message="Transaction created successfully.",
        data=TransactionOut.model_validate(result, from_attributes=True)
    )

@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionAutoCreate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    tx = service.create_with_auto_ledger(payload)
    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,
        message="Transaction created successfully",
        data=TransactionOut.model_validate(tx, from_attributes=True),
    )

@router.put("/update", response_model=ApiResponse)
def update_transaction_api(
    transaction_id: UUID = Query(...),
    user_id: UUID = Query(...),
    client_id: UUID = Query(...),
    payload: TransactionUpdate = None,
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    tx = service.update(
        transaction_id=transaction_id,
        user_id=user_id,
        client_id=client_id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Transaction updated successfully",
        data=TransactionOut.model_validate(tx, from_attributes=True),
    )

@router.delete("/delete", response_model=ApiResponse)
def delete_transaction_api(
    transaction_id: UUID = Query(...),
    user_id: UUID = Query(...),
    client_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    service.delete(tx_id=transaction_id, client_id=client_id, user_id=user_id)
    return ApiResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Transaction deleted successfully",
        data=None,
    )
