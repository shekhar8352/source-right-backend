# SourceRight Backend (Foundation)

Minimal Django + DRF backend with PostgreSQL, Redis, and Celery. The Django API runs locally (no container). Celery workers run in Docker only.

**Constraints honored**
- Django API is not containerized.
- Only Celery workers run in Docker.
- PostgreSQL and Redis are external.
- All configuration is via environment variables.

## Environment Setup

1. Create a virtual environment and install dependencies with `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. Create `.env` from the example and fill in values:

```bash
cp .env.example .env
```

Required variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

If Redis is running on your host machine, set:
- `REDIS_HOST=localhost`
- `CELERY_BROKER_URL=redis://:your_password@localhost:6379/0`
- `CELERY_RESULT_BACKEND=redis://:your_password@localhost:6379/1`

If Redis is running in Docker on a network (e.g. service name `redis`), keep the `.env` values as localhost for your local Django API, and Docker Compose will override the worker to use `redis` as the host automatically.

If PostgreSQL is running in Docker on a network (e.g. service name `postgres`), keep `.env` as localhost for your local Django API, and Docker Compose will override the worker to use `postgres` as the host automatically.

Ensure the Celery container is attached to the same Docker network as Redis/Postgres. By default this repo expects an external network named `backend`. If your Redis/Postgres compose file creates a different network name, set `BACKEND_DOCKER_NETWORK` when running Docker Compose, for example:

```bash
BACKEND_DOCKER_NETWORK=yourproject_backend docker compose up --build celery_worker
```

## Run Django API Locally

```bash
python manage.py migrate
python manage.py runserver
```

This uses `sourceright.settings.local` by default.

## Django Shell Plus

Install dependencies (if not already):

```bash
uv pip install -r requirements.txt
```

Run:

```bash
python manage.py shell_plus
```

## Start Celery Worker via Docker

```bash
docker compose up --build celery_worker
```

The worker reads `.env` and connects to external Redis and PostgreSQL.

## Run Tests

Run the full test suite:

```bash
python manage.py test
```

Run tests for a single app:

```bash
python manage.py test apps.organizations
python manage.py test apps.access_control
```

Run a single test module:

```bash
python manage.py test apps.access_control.tests.test_invites
```

Verbose output:

```bash
python manage.py test -v 2
```

## Test the Celery Task

In another shell:

```bash
python manage.py shell
```

```python
from apps.core.tasks import health_check
health_check.delay()
```

Expected result: the worker logs a successful task execution and returns `"ok"`.

## Project Structure

```
.
├── shared/
│   └── logging/
│       ├── __init__.py
│       ├── config.py
│       ├── context.py
│       ├── middleware.py
│       ├── filters.py
│       ├── formatters.py
│       └── logger.py
├── docker/
│   └── celery-entrypoint.sh
├── sourceright/
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   └── core/
│       ├── apps.py
│       └── tasks.py
├── manage.py
├── Dockerfile.celery
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Notes

- Redis is used for Django cache, Celery broker, and Celery result backend.
- `django_celery_results` and `django_celery_beat` are installed for extensibility.
- `production.py` is a placeholder for future environment hardening.

## Logging

The backend uses a single, production-grade logging system across Django and Celery. Logs are plain text and optimized for `tail -f`, `grep`, and `awk`.

Log format:

```
2026-02-03 12:34:56 | INFO | log_id=abc123 | file=invoice_service.py:87 | func=create_invoice | msg=Invoice created successfully
```

Log files:
- `logs/app.log` for Django and application logs
- `logs/celery.log` for Celery worker and task logs
- `logs/errors.log` for errors with stack traces

log_id lifecycle:
- A `log_id` is created per request by middleware.
- If a request provides `X-Log-Id`, it is reused.
- The `log_id` is propagated to Celery tasks via message headers.
- Retries keep the same `log_id`.
- Standalone tasks generate a new `log_id`.

Environment configuration:
- `LOG_LEVEL` (default `INFO`)
- `LOG_DIR` (default `logs`)
- `LOG_MAX_BYTES` (default `10485760`)
- `LOG_BACKUP_COUNT` (default `10`)
- `ENABLE_CONSOLE_LOGGING` (default `true`)

Example usage in a Django view:

```python
from django.http import JsonResponse
from shared.logging import get_logger

logger = get_logger(__name__)

def example_view(request):
    logger.info("Example view hit", extra={"path": request.path})
    return JsonResponse({"status": "ok"})
```

Example usage in a service:

```python
from shared.logging import get_logger

logger = get_logger(__name__)

def create_invoice(invoice_id, amount):
    logger.info("Invoice created", extra={"invoice_id": invoice_id, "amount": amount})
```

Example usage in a Celery task:

```python
from celery import shared_task
from shared.logging import get_logger

logger = get_logger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5)
def health_check(self):
    logger.info("Health check task started")
    return "ok"
```

Debugging tips:
1. Tail application logs: `tail -f logs/app.log`
2. Tail Celery logs: `tail -f logs/celery.log`
3. Find a trace: `grep "log_id=<value>" logs/app.log logs/celery.log`

## Health Checks

Health check endpoints live under `health/`:
- `GET /health/live` for liveness (fast, no external dependencies).
- `GET /health/ready` for readiness (checks database + Redis).

Readiness response includes per-check status and timing, and returns `503` if any check fails.
