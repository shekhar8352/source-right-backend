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
