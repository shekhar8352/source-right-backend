from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from shared.logging import get_logger

logger = get_logger(__name__)


@require_http_methods(["GET"])
def example_view(request):
    logger.info("Example view hit", extra={"path": request.path})
    return JsonResponse({"status": "ok"})
