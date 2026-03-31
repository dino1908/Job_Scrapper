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

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

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
            "Job screening will use deterministic filtering only."
        )

    for warning in warnings:
        print(f"⚠️  {warning}")


# Validate on import
validate_settings()
