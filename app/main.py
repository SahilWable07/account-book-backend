from fastapi import FastAPI
from app.api.v1.api_router import api_router
from app.core.middleware import setup_middleware
from app.core.errors import add_exception_handlers
from app.db.tables import create_tables

app = FastAPI(title="AccountBook AI")

setup_middleware(app) #
add_exception_handlers(app)

@app.on_event("startup")
def on_startup():
    create_tables() #

app.include_router(api_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to AccountBook AI"}

@app.get("/health")
def health_check():
    return {"status": "ok"}