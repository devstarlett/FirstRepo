"""Pydantic models shared across the API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User representation used for authentication."""

    username: str
    full_name: str
    disabled: bool = False


class UserInDB(User):
    """User model containing hashed password."""

    hashed_password: str


class Token(BaseModel):
    """JWT token metadata."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded inside JWT tokens."""

    username: Optional[str] = None


class IngestionPayload(BaseModel):
    """Input payload for data ingestion."""

    source: str = Field(description="Name of the upstream data source")
    metric: str = Field(description="Metric identifier", examples=["revenue"])
    value: float = Field(description="Metric value in raw units")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IngestionResponse(BaseModel):
    """Response describing persisted records."""

    rows_ingested: int
    warehouse_path: str
