"""Configuration helpers for the FastAPI service."""
from __future__ import annotations

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration derived from environment variables."""

    jwt_secret_key: str = Field(default="super-secret", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    duckdb_path: str = "data/warehouse.duckdb"
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
