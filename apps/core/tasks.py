from celery import shared_task

from shared.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5)
def health_check(self):
    logger.info("Health check task started")
    return "ok"
