from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.inventory import InventoryCreate, InventoryOut
from app.utils.inventory_utils import InventoryService

router = APIRouter()


@router.post("/", response_model=ApiResponse, status_code=201)
def create_new_inventory_item(
    inventory_in: InventoryCreate, db: Session = Depends(get_db)
):
    """
    Create a new inventory item and a corresponding transaction.
    """
    new_item, _ = InventoryService(db).create_item(inventory_in) # Unpack the tuple here
    return ApiResponse(
        success=True,
        status_code=201,
        message="Inventory item and transaction created successfully",
        data=InventoryOut.model_validate(new_item, from_attributes=True), # Pass only the inventory item
    )