from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from app.utils.transaction_filter import TransactionFilterService
from uuid import UUID
from datetime import date
from io import BytesIO
from xhtml2pdf import pisa

class StatementGenerator:
    """
    Service for generating transaction statements.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_statement_pdf(self, *, filter_type: str, user_id: UUID, client_id: UUID, start_date: date = None, end_date: date = None) -> BytesIO:
        """
        Generates a PDF statement for the given filter.
        """
        result = TransactionFilterService.filter_transactions(self.db, filter_type, user_id, client_id, start_date, end_date)
        
        if not result or not result.get("transactions"):
            return None

        env = Environment(loader=FileSystemLoader('app/template'))
        template = env.get_template('statement.html')

        html = template.render(data=result)
        
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

        if pisa_status.err:
            return None
        
        pdf_buffer.seek(0)
        return pdf_buffer