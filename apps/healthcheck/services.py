import time
import uuid
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.db import connections

from shared.logging import get_logger

logger = get_logger(__name__)


def _duration_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _result(name: str, ok: bool, duration_ms: int, error: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": name,
        "ok": ok,
        "duration_ms": duration_ms,
    }
    if error:
        payload["error"] = error
    return payload


def check_database() -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as exc:
        duration_ms = _duration_ms(start)
        logger.exception("Database health check failed", extra={"duration_ms": duration_ms})
        return _result("database", False, duration_ms, error=str(exc))

    duration_ms = _duration_ms(start)
    logger.info("Database health check ok", extra={"duration_ms": duration_ms})
    return _result("database", True, duration_ms)


def check_redis() -> Dict[str, Any]:
    start = time.perf_counter()
    key = f"healthcheck:{uuid.uuid4().hex}"
    try:
        cache.set(key, "1", timeout=5)
        value = cache.get(key)
        cache.delete(key)
        ok = value == "1"
        if not ok:
            raise RuntimeError("Cache value mismatch")
    except Exception as exc:
        duration_ms = _duration_ms(start)
        logger.exception("Redis health check failed", extra={"duration_ms": duration_ms})
        return _result("redis", False, duration_ms, error=str(exc))

    duration_ms = _duration_ms(start)
    logger.info("Redis health check ok", extra={"duration_ms": duration_ms})
    return _result("redis", True, duration_ms)
