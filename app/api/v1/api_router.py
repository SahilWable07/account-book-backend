from fastapi import APIRouter
from app.api.v1.endpoints import bank_accounts, financial_settings , ledgers , transactions, inventory , transaction_filter , user , user_management,invitation_status,funds


api_router = APIRouter()

api_router.include_router(
    bank_accounts.router,
    prefix="/accounts",
    tags=["Accounts"]
)

api_router.include_router(
    financial_settings.router,
    prefix="/accounts",
    tags=["Financial Settings"]
)

api_router.include_router(
    ledgers.router, 
    prefix="/ledgers", 
    tags=["Ledgers"]
)

api_router.include_router(
    transaction_filter.router,
    prefix="/transactions",
    tags=["Transactions"]
)   

api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"]
)  

api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["Inventory"]
)

# api_router.include_router(
#     user.router,
#     prefix="/users",
#     tags=["Users"]
# )

# api_router.include_router(
#     user_management.router,
#     prefix="/users",
#     tags=["Users"]
# )

# api_router.include_router(
#     funds.router,
#     prefix="/funds",
#     tags=["Funds Transaction"]
# )

# api_router.include_router(
#     invitation_status.router,
#     prefix="/notification",
#     tags=["Notification"]
# )