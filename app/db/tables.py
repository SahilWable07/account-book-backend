# In app/db/init_db.py

import logging
from app.db.base import Base
from app.db.session import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """
    Connects to the database and creates all tables based on the SQLAlchemy models.
    This function is called on FastAPI startup.
    """
    logger.info("Attempting to create database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        logger.error(f"An error occurred during table creation: {e}")

