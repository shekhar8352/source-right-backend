import logging
from typing import Any, Dict

_STANDARD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}

_CONTEXT_ATTRS = {"log_id", "tenant_id", "task_id", "task_name"}


class PlainTextFormatter(logging.Formatter):
    def __init__(self, datefmt: str = "%Y-%m-%d %H:%M:%S") -> None:
        super().__init__(datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        timestamp = self.formatTime(record, self.datefmt)
        log_id = getattr(record, "log_id", "-")
        base = (
            f"{timestamp} | {record.levelname} | log_id={log_id} | "
            f"file={record.filename}:{record.lineno} | func={record.funcName} | "
            f"msg={record.message}"
        )

        extra_parts = []
        tenant_id = getattr(record, "tenant_id", None)
        if tenant_id:
            extra_parts.append(f"tenant_id={tenant_id}")
        task_id = getattr(record, "task_id", None)
        if task_id:
            extra_parts.append(f"task_id={task_id}")
        task_name = getattr(record, "task_name", None)
        if task_name:
            extra_parts.append(f"task_name={task_name}")

        extra_parts.extend(self._format_extra_fields(record.__dict__))
        if extra_parts:
            base = f"{base} | " + " | ".join(extra_parts)

        if record.exc_info:
            base = base + "\n" + self.formatException(record.exc_info)

        return base

    def _format_extra_fields(self, data: Dict[str, Any]) -> list[str]:
        extras: list[str] = []
        for key, value in data.items():
            if key in _STANDARD_ATTRS or key in _CONTEXT_ATTRS:
                continue
            if key.startswith("_"):
                continue
            if value is None:
                continue
            extras.append(f"{key}={value}")
        return extras
