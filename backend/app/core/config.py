"""
Application Configuration using Pydantic Settings v2.
Reads credentials strictly from .env without exposing secrets.
"""

from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from backend.app.core.charger_config import ChargerDevice

# Locate .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
        env_ignore_empty=True
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
    SECRET_KEY: str = Field(min_length=32, repr=False)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=15)
    SECURE_COOKIES: bool = True
    CORS_ORIGINS: list[str] = []
    FRONTEND_DIRECTORY: Path | None = None
    OCPP_DEVICES: dict[int, ChargerDevice] = Field(default_factory=dict, repr=False)

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        forbidden = {
            "default_dev_secret_key_change_in_production",
            "change_this_to_a_secure_random_secret_key_in_production",
        }
        if value.strip() in forbidden or len(value.strip()) < 32:
            raise ValueError("Set SECRET_KEY to a unique random secret of at least 32 characters.")
        return value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("Credentialed CORS requires explicit origins.")
        return origins

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
