"""Tests for the FastAPI ingestion workflow."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.auth import _FAKE_USERS_DB, create_access_token
from app.config import Settings
from app.main import app
from app.models import IngestionPayload


@pytest.fixture(autouse=True)
def _reset_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(duckdb_path=str(tmp_path / "warehouse.duckdb"))
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(settings.duckdb_path) as conn:
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


def _token(settings: Settings) -> str:
    user = next(iter(_FAKE_USERS_DB.values()))
    return create_access_token({"sub": user.username}, settings)


def test_healthcheck() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(duckdb_path=str(tmp_path / "warehouse.duckdb"))
    monkeypatch.setattr("app.config.get_settings", lambda: settings)

    payload = IngestionPayload(source="pytest", metric="unit", value=1.23, timestamp=datetime.utcnow())
    client = TestClient(app)
    token = _token(settings)
    response = client.post(
        "/ingest",
        json=payload.model_dump(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rows_ingested"] == 1
    assert Path(body["warehouse_path"]).exists()

    with duckdb.connect(settings.duckdb_path) as conn:
        row = conn.execute("select * from metrics").fetchone()
    assert row[0] == payload.source
    assert row[1] == payload.metric
