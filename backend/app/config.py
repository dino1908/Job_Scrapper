"""
Application configuration management.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from base and secret env files.
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env.secrets", override=True)


class Settings:
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Job Scrapper API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # API Keys
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/job_scrapper.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # File Upload
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    UPLOAD_DIR: str = "uploads"

    # Scraping
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "300"))  # 5 minutes
    MAX_JOBS_PER_SOURCE: int = int(os.getenv("MAX_JOBS_PER_SOURCE", "50"))

    # Job Matching
    MIN_MATCH_SCORE: float = 30.0  # Minimum score to show a job

    # Rate Limiting
    RATE_LIMIT_DELAY_MIN: float = 2.0  # seconds
    RATE_LIMIT_DELAY_MAX: float = 5.0  # seconds


# Create a global settings instance
settings = Settings()


def validate_settings() -> None:
    """Validate that required settings are configured."""
    warnings = []

    if not settings.MISTRAL_API_KEY:
        warnings.append(
            "Warning: Mistral API key not configured. "
            "Resume analysis will fall back to basic extraction."
        )

    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        warnings.append(
            "Warning: Using default SECRET_KEY. "
            "Please set a random secret key in production."
        )

    for warning in warnings:
        print(f"⚠️  {warning}")


# Validate on import
validate_settings()
