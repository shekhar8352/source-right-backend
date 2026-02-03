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

## Run Django API Locally

```bash
python manage.py migrate
python manage.py runserver
```

This uses `sourceright.settings.local` by default.

## Start Celery Worker via Docker

```bash
docker compose up --build celery_worker
```

The worker reads `.env` and connects to external Redis and PostgreSQL.

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
