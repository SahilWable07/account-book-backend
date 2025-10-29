from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction
from app.models.ledger import Ledger
from enum import Enum
import uuid


class TransactionFilterService:
    """
    Service for date range computation and transaction/ledger summarization.
    Stateless utility methods are grouped here for cohesion.
    """

    @staticmethod
    def get_date_range(filter_type: str, start_date: date = None, end_date: date = None):
        today = date.today()
        if filter_type == "today":
            return today, today
        elif filter_type == "yesterday":
            y = today - timedelta(days=1)
            return y, y
        elif filter_type == "this_week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif filter_type == "last_week":
            end = today - timedelta(days=today.weekday() + 1)
            start = end - timedelta(days=6)
            return start, end
        elif filter_type == "this_month":
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
        elif filter_type == "custom" and start_date and end_date:
            return start_date, end_date
        raise ValueError("Invalid filter type or missing dates for custom filter")

    @staticmethod
    def filter_transactions(
        db: Session,
        filter_type: str,
        user_id: uuid.UUID,
        client_id: uuid.UUID,
        start_date: date = None,
        end_date: date = None,
    ):
        start, end = TransactionFilterService.get_date_range(filter_type, start_date, end_date)
        txs = (
            db.query(Transaction)
            .filter(
                func.date(Transaction.created_at) >= start,
                func.date(Transaction.created_at) <= end,
                Transaction.is_deleted == False,
                Transaction.user_id == user_id,
                Transaction.client_id == client_id,
            )
            .all()
        )
        if not txs:
            return None
        return {
            "filter": filter_type,
            "start_date": start,
            "end_date": end,
            "transactions": txs,
        }


class PeriodEnum(str, Enum):
    this_week = "this_week"
    last_week = "last_week"
    this_month = "this_month"
    last_month = "last_month"


class LedgerSummaryService:
    @staticmethod
    def get_date_range_period(period: 'PeriodEnum'):
        today = datetime.today()
        if period == PeriodEnum.this_week:
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == PeriodEnum.last_week:
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == PeriodEnum.this_month:
            start_date = today.replace(day=1)
            end_date = today
        elif period == PeriodEnum.last_month:
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start_date = last_day_last_month.replace(day=1)
            end_date = last_day_last_month
        else:
            start_date = today
            end_date = today
        return start_date, end_date

    @staticmethod
    def calculate_ledger_summary(db: Session, period: 'PeriodEnum', user_id: uuid.UUID, client_id: uuid.UUID):
        start_date, end_date = LedgerSummaryService.get_date_range_period(period)
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
                Transaction.user_id == user_id,
                Transaction.client_id == client_id,
            )
            .all()
        )
        if not transactions:
            return None
        summary = {
            "income": 0,
            "expense": 0,
            "loan_payable": 0,
            "loan_receivable": 0,
            "total": 0,
        }
        for txn in transactions:
            if txn.type == "income":
                summary["income"] += txn.amount
            elif txn.type == "expense":
                summary["expense"] += txn.amount
            elif txn.type == "loan_payable":
                summary["loan_payable"] += txn.amount
            elif txn.type == "loan_receivable":
                summary["loan_receivable"] += txn.amount
        summary["total"] = (
            summary["income"] - summary["expense"] + summary["loan_receivable"] - summary["loan_payable"]
        )
        return {
            "period": period.value,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "summary": summary,
        }

