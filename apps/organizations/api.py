from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shared.logging import get_logger

from .serializers import OrganizationCreateSerializer, OrganizationResponseSerializer
from .services.organization_service import create_organization

logger = get_logger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_organization_view(request):
    serializer = OrganizationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    organization = create_organization(creator=request.user, **serializer.validated_data)

    logger.info(
        "Organization created",
        extra={"org_id": organization.org_id, "created_by": request.user.id},
    )

    response_serializer = OrganizationResponseSerializer(organization)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
