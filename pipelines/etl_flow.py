"""Prefect flow orchestrating data ingestion from a public API."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import duckdb
import httpx
import pandas as pd
from prefect import flow, get_run_logger, task

from app.config import get_settings


API_URL = "https://api.coindesk.com/v1/bpi/currentprice.json"


@task(retries=3, retry_delay_seconds=10)
def fetch_prices() -> pd.DataFrame:
    """Fetch Bitcoin prices from Coindesk and return as DataFrame."""

    response = httpx.get(API_URL, timeout=10.0)
    response.raise_for_status()
    payload = response.json()
    rows: List[dict] = []
    for currency, metadata in payload["bpi"].items():
        rows.append(
            {
                "source": "coindesk",
                "metric": f"btc_price_{currency.lower()}",
                "value": float(metadata["rate_float"]),
                "timestamp": datetime.utcnow(),
            }
        )
    return pd.DataFrame(rows)


@task
def persist(df: pd.DataFrame) -> int:
    """Persist DataFrame records into DuckDB."""

    settings = get_settings()
    path = Path(settings.duckdb_path)
    path.parent.mkdir(exist_ok=True)
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
        conn.executemany(
            "insert into metrics values (?, ?, ?, ?)",
            cast_to_records(df.to_dict(orient="records")),
        )
    return len(df)


def cast_to_records(rows: Iterable[dict]) -> List[tuple]:
    """Convert DataFrame rows into tuples for DuckDB ingestion."""

    return [
        (row["source"], row["metric"], float(row["value"]), row["timestamp"]) for row in rows
    ]


@flow(name="bitcoin-price-etl")
def etl_flow() -> int:
    """End-to-end orchestration of the ETL job."""

    logger = get_run_logger()
    data = fetch_prices()
    rows = persist(data)
    logger.info("ETL completed", rows=rows)
    return rows


if __name__ == "__main__":
    etl_flow()
