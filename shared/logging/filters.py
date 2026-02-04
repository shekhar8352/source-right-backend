import logging

from .context import ensure_log_id, get_task_id, get_task_name, get_tenant_id


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.log_id = ensure_log_id()
        record.tenant_id = get_tenant_id()
        record.task_id = get_task_id()
        record.task_name = get_task_name()
        return True


class CeleryLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(get_task_id()) or record.name.startswith("celery")


class NotCeleryLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not (bool(get_task_id()) or record.name.startswith("celery"))
