from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from starlette import status


def _api_response(success: bool, status_code: int, message: str, data=None, error=None, meta=None):
    return {
        "success": success,
        "status_code": status_code,
        "message": message,
        "data": data,
        "error": error,
        "meta": meta,
    }


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            message = detail.get("message") or "HTTP error"
            error_obj = {"type": "HTTPException", **detail}
        else:
            message = str(detail) if detail else "HTTP error"
            error_obj = {"type": "HTTPException", "detail": detail}
        payload = _api_response(
            success=False,
            status_code=exc.status_code,
            message=message,
            data=None,
            error=error_obj,
        )
        return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(payload))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        payload = _api_response(
            success=False,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation error",
            data=None,
            error={
                "type": "RequestValidationError",
                "errors": exc.errors(),
            },
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=jsonable_encoder(payload))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        payload = _api_response(
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            data=None,
            error={
                "type": exc.__class__.__name__,
                "detail": str(exc),
            },
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(payload))


