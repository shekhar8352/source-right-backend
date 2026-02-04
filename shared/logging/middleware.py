import time
from typing import Callable

from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse

from .context import generate_log_id, reset_log_id, set_log_id
from .logger import get_logger


class LoggingMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger("request")
        self._is_async = iscoroutinefunction(get_response)

    async def __call__(self, request: HttpRequest) -> HttpResponse:
        if self._is_async:
            return await self._call_async(request)
        return self._call_sync(request)

    def _set_context(self, request: HttpRequest):
        incoming_log_id = request.headers.get("X-Log-Id")
        if incoming_log_id:
            return set_log_id(incoming_log_id)
        return set_log_id(generate_log_id())

    def _log_start(self, request: HttpRequest) -> None:
        self.logger.info(
            "Request start",
            extra={
                "method": request.method,
                "path": request.path,
            },
        )

    def _log_end(self, request: HttpRequest, status_code: int, duration_ms: int) -> None:
        self.logger.info(
            "Request end",
            extra={
                "method": request.method,
                "path": request.path,
                "status": status_code,
                "duration_ms": duration_ms,
            },
        )

    def _call_sync(self, request: HttpRequest) -> HttpResponse:
        token = self._set_context(request)
        start = time.perf_counter()
        self._log_start(request)
        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.logger.exception(
                "Request error",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log_end(request, response.status_code, duration_ms)
            return response
        finally:
            reset_log_id(token)

    async def _call_async(self, request: HttpRequest) -> HttpResponse:
        token = self._set_context(request)
        start = time.perf_counter()
        self._log_start(request)
        try:
            response = await self.get_response(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.logger.exception(
                "Request error",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log_end(request, response.status_code, duration_ms)
            return response
        finally:
            reset_log_id(token)
