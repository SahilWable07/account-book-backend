from typing import Any, Optional, Dict
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    status_code: int
    message: str
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


