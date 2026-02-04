import os

from celery import Celery
from celery.signals import before_task_publish, setup_logging, task_postrun, task_prerun

from shared.logging.config import configure_logging
from shared.logging.context import (
    ensure_log_id,
    generate_log_id,
    get_tenant_id,
    reset_log_id,
    reset_task_id,
    reset_task_name,
    reset_tenant_id,
    set_log_id,
    set_task_id,
    set_task_name,
    set_tenant_id,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sourceright.settings.local")

app = Celery("sourceright")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.worker_hijack_root_logger = False


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_logging()


@before_task_publish.connect
def inject_log_context(headers=None, **kwargs):
    if headers is None:
        return
    log_id = ensure_log_id()
    headers.setdefault("log_id", log_id)
    tenant_id = get_tenant_id()
    if tenant_id:
        headers.setdefault("tenant_id", tenant_id)


@task_prerun.connect
def bind_task_context(task_id=None, task=None, **kwargs):
    headers = getattr(task.request, "headers", {}) or {}
    log_id = headers.get("log_id") or generate_log_id()
    task.request._log_id_token = set_log_id(log_id)

    tenant_id = headers.get("tenant_id")
    if tenant_id:
        task.request._tenant_id_token = set_tenant_id(tenant_id)

    task.request._task_id_token = set_task_id(task_id or getattr(task.request, "id", None))
    task.request._task_name_token = set_task_name(getattr(task, "name", None))


@task_postrun.connect
def clear_task_context(task=None, **kwargs):
    if task is None:
        return
    request = getattr(task, "request", None)
    if request is None:
        return

    token = getattr(request, "_task_name_token", None)
    if token is not None:
        reset_task_name(token)
    token = getattr(request, "_task_id_token", None)
    if token is not None:
        reset_task_id(token)
    token = getattr(request, "_tenant_id_token", None)
    if token is not None:
        reset_tenant_id(token)
    token = getattr(request, "_log_id_token", None)
    if token is not None:
        reset_log_id(token)
