from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import serializers, status
from drf_spectacular.utils import extend_schema

from shared.logging import get_logger

from .services import check_database, check_redis

logger = get_logger(__name__)

class HealthLiveSerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()


class HealthCheckResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    ok = serializers.BooleanField()
    duration_ms = serializers.IntegerField()
    error = serializers.CharField(required=False, allow_blank=True)


class HealthReadySerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    checks = HealthCheckResultSerializer(many=True)

@extend_schema(
    summary="Health live check",
    description="Liveness probe used to verify the service process is running.",
    responses={200: HealthLiveSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def live(request):
    """Return a basic liveness probe response with server timestamp."""
    logger.info("Health live check")
    return Response(
        {"status": "ok", "timestamp": timezone.now().isoformat()},
        status=status.HTTP_200_OK,
    )

@extend_schema(
    summary="Health ready check",
    description="Readiness probe that validates database and Redis connectivity.",
    responses={
        200: HealthReadySerializer,
        503: HealthReadySerializer,
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def ready(request):
    """Return readiness probe status including database and Redis checks."""
    logger.info("Health ready check start")

    checks = [check_database(), check_redis()]
    ok = all(check["ok"] for check in checks)
    overall_status = "ok" if ok else "error"

    logger.info("Health ready check end", extra={"status": overall_status})

    return Response(
        {
            "status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "checks": checks,
        },
        status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
