# In app/db/base.py

from app.db.base_class import Base

# Import all models so that Alembic/metadata can discover them.
# These imports should come after Base is defined in base_class to avoid circular imports.
from app.models.financial_settings import FinancialSettings  # noqa: F401
from app.models.ledger import Ledger  # noqa: F401
from app.models.bank_account import BankAccount  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.invitation import Invitation  # noqa: F401
