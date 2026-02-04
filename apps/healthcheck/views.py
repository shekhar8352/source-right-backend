from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from shared.logging import get_logger

from .services import check_database, check_redis

logger = get_logger(__name__)


@require_http_methods(["GET"])
def live(request):
    logger.info("Health live check")
    return JsonResponse({"status": "ok", "timestamp": timezone.now().isoformat()})


@require_http_methods(["GET"])
def ready(request):
    logger.info("Health ready check start")

    checks = [check_database(), check_redis()]
    ok = all(check["ok"] for check in checks)
    status = "ok" if ok else "error"

    logger.info("Health ready check end", extra={"status": status})

    return JsonResponse(
        {
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "checks": checks,
        },
        status=200 if ok else 503,
    )
