"""Celery application configured to run analytic workloads."""
from __future__ import annotations

import os

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "data_platform",
    broker=os.environ.get("CELERY_BROKER_URL", settings.redis_url),
    backend=os.environ.get("CELERY_RESULT_BACKEND", settings.redis_url),
)
celery_app.conf.task_track_started = True
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="reports.generate_summary")
def generate_summary(metric: str) -> dict:
    """Compute basic aggregates for a metric stored in DuckDB."""

    from pathlib import Path

    import duckdb

    path = Path(settings.duckdb_path)
    with duckdb.connect(str(path)) as conn:
        result = conn.execute(
            """
            select metric, count(*) as records, avg(value) as average, max(timestamp) as last_seen
            from metrics
            where metric = ?
            group by metric
            """,
            (metric,),
        ).fetchone()
    if result is None:
        return {"metric": metric, "records": 0, "average": None, "last_seen": None}
    return {
        "metric": result[0],
        "records": int(result[1]),
        "average": float(result[2]),
        "last_seen": result[3].isoformat() if result[3] else None,
    }
