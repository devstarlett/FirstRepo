# API Overview

## Authentication

Obtain a token by sending a POST request to `/token` with form fields `username` and `password`.
Use the returned bearer token in the `Authorization` header for subsequent requests.

## Endpoints

### `POST /ingest`
Ingest a metric payload into the DuckDB warehouse.

### `GET /health`
Check service health.
