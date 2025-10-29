import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Application settings loaded from environment variables.
    """
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")

    
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

   
    AUTH_API_URL: str = os.getenv("AUTH_API_URL", "")

    # AI / Gemini
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_API_URL: str = os.getenv(
        "GEMINI_API_URL",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
    )

    # Business rules
    MAX_TRANSACTIONS_PER_DAY: int = int(os.getenv("MAX_TRANSACTIONS_PER_DAY", "15"))

settings = Settings()

if not all([settings.DB_PASSWORD, settings.DB_NAME]):
    raise ValueError("Missing database credentials in .env file. Please set DB_PASSWORD and DB_NAME.")
