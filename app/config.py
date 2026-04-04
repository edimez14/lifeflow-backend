from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_hours: int = Field(alias="ACCESS_TOKEN_EXPIRE_HOURS")
    server_host: str = Field(alias="SERVER_HOST")
    server_port: int = Field(alias="SERVER_PORT")
    debug: bool = Field(alias="DEBUG")

    smtp_host: str = Field(alias="SMTP_HOST")
    smtp_port: int = Field(alias="SMTP_PORT")
    smtp_user: str = Field(alias="SMTP_USER")
    smtp_password: str = Field(alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(alias="SMTP_FROM_EMAIL")

    firebase_credentials_path: str = Field(alias="FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: str = Field(alias="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: str = Field(alias="FIREBASE_STORAGE_BUCKET")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings()


settings = get_settings()
