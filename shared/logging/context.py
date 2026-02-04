import contextvars
import uuid
from typing import Optional

_log_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("log_id", default=None)
_tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
_task_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("task_id", default=None)
_task_name_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("task_name", default=None)


def generate_log_id() -> str:
    return uuid.uuid4().hex


def get_log_id() -> Optional[str]:
    return _log_id_var.get()


def set_log_id(value: str) -> contextvars.Token:
    return _log_id_var.set(value)


def reset_log_id(token: contextvars.Token) -> None:
    _log_id_var.reset(token)


def ensure_log_id() -> str:
    log_id = _log_id_var.get()
    if log_id:
        return log_id
    log_id = generate_log_id()
    _log_id_var.set(log_id)
    return log_id


def get_tenant_id() -> Optional[str]:
    return _tenant_id_var.get()


def set_tenant_id(value: str) -> contextvars.Token:
    return _tenant_id_var.set(value)


def reset_tenant_id(token: contextvars.Token) -> None:
    _tenant_id_var.reset(token)


def get_task_id() -> Optional[str]:
    return _task_id_var.get()


def set_task_id(value: Optional[str]) -> contextvars.Token:
    return _task_id_var.set(value)


def reset_task_id(token: contextvars.Token) -> None:
    _task_id_var.reset(token)


def get_task_name() -> Optional[str]:
    return _task_name_var.get()


def set_task_name(value: Optional[str]) -> contextvars.Token:
    return _task_name_var.set(value)


def reset_task_name(token: contextvars.Token) -> None:
    _task_name_var.reset(token)
