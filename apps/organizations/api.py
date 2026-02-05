from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from shared.logging import get_logger

from .domain.enums import RoleType
from .serializers import (
    OrganizationCreateSerializer,
    OrganizationInviteAcceptSerializer,
    OrganizationInviteCreateSerializer,
    OrganizationInviteResponseSerializer,
    OrganizationResponseSerializer,
)
from .services.invite_service import accept_invite, invite_user
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite_user_view(request):
    if getattr(request, "organization", None) is None:
        return Response(
            {"detail": "Organization context is required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if getattr(request, "organization_role", None) != RoleType.ORG_ADMIN:
        return Response(
            {"detail": "Only organization admins can invite users."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = OrganizationInviteCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        invite = invite_user(
            org=request.organization,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(
        "Organization invite created",
        extra={"org_id": request.organization.org_id, "email": invite.email},
    )

    response_serializer = OrganizationInviteResponseSerializer(invite)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def accept_invite_view(request):
    serializer = OrganizationInviteAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        invite = accept_invite(
            token=serializer.validated_data["token"],
            password=serializer.validated_data["password"],
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(
        "Organization invite accepted",
        extra={"org_id": invite.org_id, "email": invite.email},
    )

    return Response(
        {"status": invite.status, "org_id": invite.org_id},
        status=status.HTTP_200_OK,
    )
