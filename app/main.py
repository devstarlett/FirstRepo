"""Main FastAPI application exposing secured ingestion endpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import duckdb
import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from .auth import Token, get_current_user, login_for_access_token
from .config import Settings, get_settings
from .models import IngestionPayload, IngestionResponse, User

logger = structlog.get_logger()

app = FastAPI(title="Modern Data Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _configure_tracing() -> None:
    """Configure OpenTelemetry tracing when the app starts."""

    provider = TracerProvider(
        resource=Resource(attributes={SERVICE_NAME: "data-platform-api"})
    )
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    logger.info("tracing.initialized")


@app.post("/token", response_model=Token)
async def login(token: Token = Depends(login_for_access_token)) -> Token:
    """Exchange credentials for a bearer token."""

    logger.info("auth.login.success")
    return token


def _ensure_warehouse(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(path)) as conn:
        conn.execute(
            """
            create table if not exists metrics (
                source varchar,
                metric varchar,
                value double,
                timestamp timestamp
            )
            """
        )


@app.post("/ingest", response_model=IngestionResponse)
async def ingest(
    payload: IngestionPayload,
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> IngestionResponse:
    """Persist metrics into DuckDB and return metadata about the operation."""

    logger.info("ingest.request", user=user.username, **payload.model_dump())
    db_path = Path(settings.duckdb_path)
    _ensure_warehouse(db_path)

    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            "insert into metrics values (?, ?, ?, ?)",
            (
                payload.source,
                payload.metric,
                payload.value,
                payload.timestamp,
            ),
        )
    logger.info("ingest.persisted", warehouse=str(db_path))
    return IngestionResponse(rows_ingested=1, warehouse_path=str(db_path))


@app.get("/health", response_model=Dict[str, Any])
async def health() -> Dict[str, Any]:
    """Simple health-check endpoint."""

    return {"status": "ok"}
