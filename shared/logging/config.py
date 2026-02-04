import logging.config
import os
from pathlib import Path
from typing import Any, Dict, Optional


def _parse_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value for ENABLE_CONSOLE_LOGGING: {value}")


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def build_logging_config(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "logs")
    max_bytes = _parse_int(os.getenv("LOG_MAX_BYTES"), 10 * 1024 * 1024)
    backup_count = _parse_int(os.getenv("LOG_BACKUP_COUNT"), 10)
    enable_console = _parse_bool(os.getenv("ENABLE_CONSOLE_LOGGING"), default=True)

    if not os.path.isabs(log_dir):
        base = base_dir or Path.cwd()
        log_dir = str(base / log_dir)

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    handlers: Dict[str, Any] = {
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "plain",
            "filename": os.path.join(log_dir, "app.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "filters": ["context", "non_celery"],
        },
        "celery_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "plain",
            "filename": os.path.join(log_dir, "celery.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "filters": ["context", "celery_only"],
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "plain",
            "filename": os.path.join(log_dir, "errors.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "filters": ["context"],
        },
    }

    if enable_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "plain",
            "filters": ["context"],
            "stream": "ext://sys.stdout",
        }

    root_handlers = ["app_file", "celery_file", "error_file"]
    if enable_console:
        root_handlers.append("console")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "context": {"()": "shared.logging.filters.ContextFilter"},
            "celery_only": {"()": "shared.logging.filters.CeleryLogFilter"},
            "non_celery": {"()": "shared.logging.filters.NotCeleryLogFilter"},
        },
        "formatters": {
            "plain": {"()": "shared.logging.formatters.PlainTextFormatter"},
        },
        "handlers": handlers,
        "root": {
            "level": log_level,
            "handlers": root_handlers,
        },
        "loggers": {
            "django": {"level": log_level, "propagate": True},
            "django.request": {"level": log_level, "propagate": True},
            "celery": {"level": log_level, "propagate": True},
            "celery.app.trace": {"level": log_level, "propagate": True},
            "celery.worker": {"level": log_level, "propagate": True},
        },
    }


def configure_logging(base_dir: Optional[Path] = None) -> None:
    logging.config.dictConfig(build_logging_config(base_dir=base_dir))
