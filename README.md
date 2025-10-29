## AccountBook AI

Multi-tenant, AI-powered personal and group finance management system built with FastAPI and SQLAlchemy.

### Key Features
- AI transaction router (natural language → structured entries)
- Multi-tenant (`client_id`) and multi-user (`user_id`) scoping
- Ledgers, bank/cash accounts, transactions, inventory
- Real-time dashboard aggregations
- Standardized API responses (success/error) across the app

### Tech Stack
- FastAPI, Pydantic v2
- SQLAlchemy ORM
- Uvicorn

---

## Project Structure
```text
app/
  main.py                    # FastAPI app setup, middleware, error handlers, startup
  api/
    v1/
      api_router.py          # v1 router aggregator
      endpoints/
        bank_accounts.py     # Bank & Cash account APIs (standard ApiResponse)
        # (add more: ledgers.py, transactions.py, inventory.py, etc.)
  core/
    config.py                # Settings (env)
    middleware.py            # CORS and other middlewares
    errors.py                # Global exception handlers → standardized errors
  db/
    base_class.py            # SQLAlchemy Base (isolated to avoid circular imports)
    base.py                  # Imports models so metadata is discoverable
    session.py               # Engine and session factory
    tables.py                # create_tables() on startup
  models/
    bank_account.py          # Includes client_id, user_id
    ledger.py                # Includes client_id, user_id
    transaction.py           # Includes client_id, user_id
    inventory.py             # Includes client_id, user_id
    financial_settings.py    # Includes client_id, user_id
  schemas/
    common.py                # ApiResponse model
    bank_account.py          # Request/response schemas (Pydantic v2 from_attributes)
  services/
    transaction_service.py   # (placeholder for business logic)
  utils/
    bank_accounts.py         # get_or_create_cash_account utility
```

---

## Getting Started

### Prerequisites
- Python 3.10+

### Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file at the project root:
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/accountbook
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
APP_ENV=local
```

### Run
```bash
venv\Scripts\activate && uvicorn app.main:app --reload
```

Open API docs: http://127.0.0.1:8000/docs

---

## API Conventions

### Standard Response (success)
```json
{
  "success": true,
  "status_code": 200,
  "message": "...",
  "data": { /* payload */ },
  "error": null,
  "meta": null
}
```

### Standard Response (error)
Errors are normalized globally by `app/core/errors.py`.
```json
{
  "success": false,
  "status_code": 409,
  "message": "Cash account already exists for this user in this group.",
  "data": null,
  "error": {
    "type": "HTTPException",
    "code": "CASH_ACCOUNT_EXISTS",
    "message": "Cash account already exists for this user in this group."
  },
  "meta": null
}
```

### Multi-Tenancy
- All create/read operations must include `client_id` and `user_id` (UUIDs) and queries filter by both.

---

## Endpoints (v1)

Base path: `/api/v1`

### Bank Accounts

- Create bank account
  - POST `/bank-accounts/bank`
  - Body:
    ```json
    {
      "client_id": "uuid",
      "user_id": "uuid",
      "account_name": "SBI Savings",
      "bank_name": "SBI",
      "account_type": "bank",
      "balance": 15000
    }
    ```
  - Response: Standard `ApiResponse` with created account in `data` (201).

- Create cash account (one per group/user)
  - POST `/bank-accounts/cash`
  - Body:
    ```json
    {
      "client_id": "uuid",
      "user_id": "uuid",
      "balance": 0
    }
    ```
  - Success (created): 201 with account in `data`.
  - Error (already exists): 409 with standardized error (code `CASH_ACCOUNT_EXISTS`).

- List accounts by group and user
  - GET `/bank-accounts/{client_id}/{user_id}`
  - Response: `ApiResponse` with a list of accounts in `data` (200).

> Other modules (ledgers, transactions, inventory, financial settings) follow the same multi-tenant pattern and standardized responses.

---

## Notes
- Pydantic v2: Output schemas that use `.from_orm()` set `Config.from_attributes = True`.
- Circular import prevention: `Base` lives in `app/db/base_class.py`; `app/db/base.py` imports models for metadata discovery.
- Global error formatting is applied via `add_exception_handlers(app)` in `main.py`.

---

## Example cURL

Create cash account (may return 201 or 409):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/bank-accounts/cash" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "3fa85f64-5717-4562-b3fc-2c963f66afa5",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa5",
    "balance": 900
  }'
```

List accounts:
```bash
curl "http://127.0.0.1:8000/api/v1/bank-accounts/3fa85f64-5717-4562-b3fc-2c963f66afa5/3fa85f64-5717-4562-b3fc-2c963f66afa5"
```
