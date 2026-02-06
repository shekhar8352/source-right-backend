from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from shared.logging import get_logger

from .serializers import CoreExampleResponseSerializer

logger = get_logger(__name__)


@extend_schema(
    summary="Example endpoint",
    description="Example API endpoint used for smoke testing.",
    responses={200: CoreExampleResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def example_view(request):
    """Return a basic OK response for smoke testing."""
    logger.info("Example view hit", extra={"path": request.path})
    return Response({"status": "ok"}, status=status.HTTP_200_OK)
