# Modern Python Data Platform

This repository contains a reference implementation of a modern, end-to-end data platform
built with Python. It demonstrates how to combine an API layer, orchestration, asynchronous
workers, a metrics warehouse, analytics dashboards, and CI/CD automation into a cohesive
project that showcases quality and complexity.

## Architecture Overview

```
FastAPI API  --->  DuckDB Warehouse  <---  Prefect ETL
        |                         ^
        |                         |
   Celery Workers --------> Streamlit Dashboard
```

### API + Authentication Layer

- FastAPI service exposes secured endpoints for ingesting metrics.
- JWT-based authentication using OAuth2 password flow.
- Structured logging and OpenTelemetry tracing out of the box.

Run locally:

```bash
uvicorn app.main:app --reload
```

Retrieve a token:

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=data.engineer&password=changeme"
```

Ingest data:

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"source": "cli", "metric": "demo", "value": 42.0}'
```

### Data Processing Pipeline

- Prefect orchestrates ETL that fetches Bitcoin price data from Coindesk and loads it into DuckDB.
- Resilient retry behavior with clear logging.

Run the flow:

```bash
python -m pipelines.etl_flow
```

### Asynchronous Workers

- Celery workers use Redis for the broker/backend and compute aggregated reports.
- Flower can monitor the workers when launched with `celery -A worker.celery_app flower`.

Start a worker locally:

```bash
celery -A worker.celery_app worker --loglevel=info
```

Trigger a task:

```python
from worker.celery_app import generate_summary
result = generate_summary.delay("btc_price_usd")
print(result.get(timeout=10))
```

### Analytics & Visualization

- Streamlit dashboard renders tables, interactive Plotly charts, and anomaly alerts.

Run the dashboard:

```bash
streamlit run dashboards/app.py
```

### CI/CD & Quality Gates

- `pytest` for unit tests, `mypy` for static typing, and `ruff` for linting.
- GitHub Actions workflow executes the quality gates on every push/PR.

Run locally:

```bash
pytest
mypy .
ruff check .
```

### Documentation & Observability

- Markdown docs in `docs/` with API overview.
- Structured logging via `structlog` and tracing via OpenTelemetry console exporter.

## Project Layout

- `app/` – FastAPI service and authentication utilities.
- `pipelines/` – Prefect ETL flow.
- `worker/` – Celery application with analytic tasks.
- `dashboards/` – Streamlit dashboard.
- `docs/` – Additional documentation.
- `tests/` – Automated tests with pytest.

## Local Development

1. Create a virtual environment and install dependencies (Poetry or `pip install -r`).
2. Copy `.env.example` if you add one, set secrets.
3. Run `uvicorn app.main:app --reload` to start the API.
4. Launch supporting services (Redis, Prefect Orion, Streamlit) as needed.

## Extending the Platform

- Add more Prefect flows for upstream sources.
- Integrate dbt for warehouse transformations.
- Swap DuckDB for Snowflake or BigQuery by adapting connection logic.
- Add Grafana dashboards backed by Prometheus metrics.
