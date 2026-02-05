# Healthcheck App

Health endpoints for service liveness and readiness. These endpoints are intentionally lightweight and should never expose sensitive data.

## Endpoints
- `GET /health/live` — Liveness probe
- `GET /health/ready` — Readiness probe (DB + Redis checks)

## Notes
- Keep checks fast and non-blocking.
- Avoid adding business logic here.
