#!/usr/bin/env sh
set -e

: "${REDIS_HOST:?Missing REDIS_HOST}"
: "${REDIS_PORT:?Missing REDIS_PORT}"
: "${REDIS_DB:?Missing REDIS_DB}"
: "${POSTGRES_HOST:?Missing POSTGRES_HOST}"
: "${POSTGRES_PORT:?Missing POSTGRES_PORT}"

CELERY_RESULT_DB="${CELERY_RESULT_DB:-1}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
CELERY_LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"

if [ -n "${REDIS_PASSWORD:-}" ]; then
  REDIS_AUTH=":${REDIS_PASSWORD}@"
else
  REDIS_AUTH=""
fi

if [ -z "${CELERY_BROKER_URL:-}" ]; then
  export CELERY_BROKER_URL="redis://${REDIS_AUTH}${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
fi

if [ -z "${CELERY_RESULT_BACKEND:-}" ]; then
  export CELERY_RESULT_BACKEND="redis://${REDIS_AUTH}${REDIS_HOST}:${REDIS_PORT}/${CELERY_RESULT_DB}"
fi

python - <<'PY'
import os
import socket
import time

def wait_for(name, host, port, max_wait=60):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{name} is available")
                return
        except OSError as exc:
            if time.time() - start > max_wait:
                raise SystemExit(f"Timed out waiting for {name}: {exc}")
            print(f"Waiting for {name} ({exc})...")
            time.sleep(2)

wait_for("Redis", os.environ["REDIS_HOST"], int(os.environ["REDIS_PORT"]))
wait_for("Postgres", os.environ["POSTGRES_HOST"], int(os.environ["POSTGRES_PORT"]))
PY

if [ "${RUN_MIGRATIONS}" = "1" ] || [ "${RUN_MIGRATIONS}" = "true" ]; then
  python manage.py migrate --noinput
fi

exec celery -A sourceright worker -l "${CELERY_LOG_LEVEL}"
