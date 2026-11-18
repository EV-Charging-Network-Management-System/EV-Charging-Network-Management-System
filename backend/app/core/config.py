"""
Application Configuration using Pydantic Settings v2.
Reads credentials strictly from .env without exposing secrets.
"""

from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "EV Charging Network Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database Configuration (PostgreSQL 18)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ev_charging_network"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SSLMODE: str = "prefer"
    DATABASE_URL: Optional[str] = None

    # Connection Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 1800

    # Security
    SECRET_KEY: str = "default_dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALLOW_DEMO_PASSWORDS: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def sync_database_url(self) -> str:
        """
        Returns SQLAlchemy 2.x connection URL using the psycopg 3 driver:
        postgresql+psycopg://user:password@host:port/dbname
        """
        if self.DATABASE_URL:
            # Normalize driver prefix if needed
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            return url

        pwd_escaped = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+psycopg://{self.DB_USER}:{pwd_escaped}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()

