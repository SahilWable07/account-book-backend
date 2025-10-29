from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
import uuid
from app.db.session import get_db
from app.utils.transaction_filter import (
    TransactionFilterService,
    LedgerSummaryService,
    PeriodEnum,
)
from fastapi.responses import StreamingResponse
from app.utils.statement_generator import StatementGenerator
from io import BytesIO

router = APIRouter()


@router.get("/history")
def filter_transactions_api(
    filter_type: str = Query(..., regex="^(today|yesterday|this_week|last_week|this_month|custom)$"),
    user_id: uuid.UUID = Query(..., description="User ID"),
    client_id: uuid.UUID = Query(..., description="Group ID"),
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
):
    result = TransactionFilterService.filter_transactions(db, filter_type, user_id, client_id, start_date, end_date)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found for this user_id and client_id",
        )
    return {"success": True, "data": result}


@router.get("/total_balance")
def get_ledger_summary(
    period: PeriodEnum = Query(..., description="Select period (dropdown)"),
    user_id: uuid.UUID = Query(..., description="User ID"),
    client_id: uuid.UUID = Query(..., description="Group ID"),
    db: Session = Depends(get_db),
):
    result = LedgerSummaryService.calculate_ledger_summary(db, period, user_id, client_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ledger summary found for this user_id and client_id",
        )
    return {"success": True, "data": result}


@router.get("/download_statement")
def download_statement_api(
    filter_type: str = Query(..., regex="^(yesterday|this_week|this_month)$"),
    user_id: uuid.UUID = Query(..., description="User ID"),
    client_id: uuid.UUID = Query(..., description="Group ID"),
    db: Session = Depends(get_db),
):
    """
    Download a transaction statement as a PDF.
    """
    generator = StatementGenerator(db)
    pdf_buffer = generator.generate_statement_pdf(
        filter_type=filter_type, 
        user_id=user_id, 
        client_id=client_id
    )

    if not pdf_buffer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found for the selected period.",
        )

    return StreamingResponse(
        iter([pdf_buffer.read()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=statement.pdf"}
    )