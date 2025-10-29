
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.financial_settings import FinancialSettingsCreate, FinancialSettingsResponse
from app.schemas.common import ApiResponse
from app.utils.financial_settings import FinancialSettingsService

router = APIRouter()

@router.post("/financial_settings", response_model=ApiResponse, status_code=201)
def create_financial_settings_api(payload: FinancialSettingsCreate, db: Session = Depends(get_db)):
    service = FinancialSettingsService(db)
    created_settings = service.create(payload)
    return ApiResponse(
        success=True,
        status_code=201,
        message="Financial settings created successfully",
        data={"id": str(created_settings.id)}
    )

@router.get("/financial_settings", response_model=ApiResponse)
def get_financial_settings_api(
    user_id: uuid.UUID = Query(..., description="User ID"),
    client_id: uuid.UUID = Query(..., description="Group ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    service = FinancialSettingsService(db)
    settings = service.list_by_user(user_id, client_id, limit=limit, offset=offset)
    
    if not settings:
        return ApiResponse(
            success=True,
            status_code=200,
            message="No financial settings found",
            data=[]
        )

    return ApiResponse(
        success=True,
        status_code=200,
        message="Financial settings fetched successfully",
        data=[FinancialSettingsResponse.model_validate(s, from_attributes=True) for s in settings]
    )
