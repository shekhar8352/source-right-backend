from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5)
def health_check(self):
    return "ok"
