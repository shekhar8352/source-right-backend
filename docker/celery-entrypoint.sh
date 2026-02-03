#!/usr/bin/env sh
set -e

: "${REDIS_HOST:?Missing REDIS_HOST}"
: "${REDIS_PORT:?Missing REDIS_PORT}"
: "${REDIS_DB:?Missing REDIS_DB}"
: "${CELERY_BROKER_URL:?Missing CELERY_BROKER_URL}"
: "${CELERY_RESULT_BACKEND:?Missing CELERY_RESULT_BACKEND}"

python - <<'PY'
import os
import socket
import time

host = os.environ.get("REDIS_HOST")
port = int(os.environ.get("REDIS_PORT", "6379"))

max_wait = 60
start = time.time()

while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("Redis is available")
            break
    except OSError as exc:
        if time.time() - start > max_wait:
            raise SystemExit(f"Timed out waiting for Redis: {exc}")
        print(f"Waiting for Redis ({exc})...")
        time.sleep(2)
PY

python manage.py migrate --noinput

exec celery -A sourceright worker -l info
