from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from shared.logging import get_logger

from apps.access_control.domain.enums import RoleType
from apps.accounts.models import UserStatus
from apps.access_control.serializers import (
    OrganizationInviteAcceptSerializer,
    OrganizationInviteCreateSerializer,
    OrganizationInviteResponseSerializer,
)
from apps.access_control.services.invite_service import accept_invite, invite_user
from apps.access_control.models import UserRole

from .serializers import (
    OrganizationCreateSerializer,
    OrganizationInviteAcceptResponseSerializer,
    OrganizationResponseSerializer,
    OrganizationSettingsSerializer,
    OrganizationSettingsUpdateSerializer,
    OrganizationUserSerializer,
)
from .services.organization_service import create_organization
from .utils import build_user_payload, get_user_role, is_last_active_admin, require_org_admin

logger = get_logger(__name__)
User = get_user_model()


@extend_schema(
    summary="Create organization",
    description=(
        "Create a new organization. If unauthenticated, provide created_by_id or "
        "creator credentials (creator_username, creator_email, creator_password)."
    ),
    request=OrganizationCreateSerializer,
    responses={201: OrganizationResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_organization_view(request):
    """Create a new organization."""
    serializer = OrganizationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    created_by_id = serializer.validated_data.pop("created_by_id", None)
    creator_username = serializer.validated_data.pop("creator_username", None)
    creator_email = serializer.validated_data.pop("creator_email", None)
    creator_password = serializer.validated_data.pop("creator_password", None)
    creator_first_name = serializer.validated_data.pop("creator_first_name", "")
    creator_last_name = serializer.validated_data.pop("creator_last_name", "")
    creator = request.user if request.user.is_authenticated else None
    organization = None
    if creator is None:
        if not created_by_id:
            if not creator_username or not creator_email or not creator_password:
                return Response(
                    {
                        "detail": "created_by_id or creator credentials are required "
                        "for unauthenticated requests."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                with transaction.atomic():
                    creator = User(
                        username=creator_username,
                        email=creator_email,
                        primary_role=RoleType.ORG_ADMIN,
                        first_name=creator_first_name,
                        last_name=creator_last_name,
                    )
                    creator.set_password(creator_password)
                    creator.save()
                    organization = create_organization(
                        creator=creator, **serializer.validated_data
                    )
            except IntegrityError:
                return Response(
                    {"detail": "Username or email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                creator = User.objects.get(id=created_by_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found for created_by_id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    if creator is None:
        return Response(
            {"detail": "Creator is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if creator.primary_role != RoleType.ORG_ADMIN:
        return Response(
            {"detail": "Only ORG_ADMIN users can create organizations."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if organization is None:
        organization = create_organization(creator=creator, **serializer.validated_data)

    logger.info(
        "Organization created",
        extra={"org_id": organization.org_id, "created_by": request.user.id},
    )

    response_serializer = OrganizationResponseSerializer(organization)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Organization settings",
    description="Read or update organization settings. Only org admins can update.",
    request=OrganizationSettingsUpdateSerializer,
    responses={200: OrganizationSettingsSerializer},
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def organization_settings_view(request):
    """Read or update organization settings."""
    if getattr(request, "organization", None) is None:
        return Response(
            {"detail": "Organization context is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    organization = request.organization
    if request.method == "GET":
        serializer = OrganizationSettingsSerializer(
            {
                "org_id": organization.org_id,
                "base_currency": organization.base_currency,
                "country": organization.country,
                "timezone": organization.timezone,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    guard = require_org_admin(request)
    if guard:
        return guard

    serializer = OrganizationSettingsUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    for field, value in serializer.validated_data.items():
        setattr(organization, field, value)
    organization.save(update_fields=list(serializer.validated_data.keys()))

    response_serializer = OrganizationSettingsSerializer(
        {
            "org_id": organization.org_id,
            "base_currency": organization.base_currency,
            "country": organization.country,
            "timezone": organization.timezone,
        }
    )
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="List organization users",
    description="List all users belonging to the current organization (admin-only).",
    responses={200: OrganizationUserSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_organization_users_view(request):
    """List users in the current organization."""
    guard = require_org_admin(request)
    if guard:
        return guard

    roles_qs = (
        UserRole.objects.filter(org_id=request.organization.org_id)
        .select_related("user")
        .order_by("user_id", "role")
    )

    user_map = {}
    for membership in roles_qs:
        user = membership.user
        if user.id in user_map:
            continue
        user_map[user.id] = build_user_payload(user, membership.role)

    users = list(user_map.values())

    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(users, request)
    serializer = OrganizationUserSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    summary="Deactivate organization user",
    description="Deactivate a user in the current organization (admin-only).",
    responses={200: OrganizationUserSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_organization_user_view(request, user_id: int):
    """Deactivate a user in the current organization."""
    guard = require_org_admin(request)
    if guard:
        return guard

    membership = (
        UserRole.objects.filter(org_id=request.organization.org_id, user_id=user_id)
        .select_related("user")
        .first()
    )
    if membership is None:
        return Response({"detail": "User not found in organization."}, status=404)

    user = membership.user
    if user.id == request.user.id and is_last_active_admin(request.organization.org_id, user.id):
        return Response(
            {"detail": "Cannot deactivate the last active organization admin."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if user.is_active or user.status != UserStatus.INACTIVE:
        user.is_active = False
        user.status = UserStatus.INACTIVE
        user.save(update_fields=["is_active", "status"])

    role = get_user_role(request.organization.org_id, user.id)
    serializer = OrganizationUserSerializer(build_user_payload(user, role))
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Reactivate organization user",
    description="Reactivate a user in the current organization (admin-only).",
    responses={200: OrganizationUserSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reactivate_organization_user_view(request, user_id: int):
    """Reactivate a user in the current organization."""
    guard = require_org_admin(request)
    if guard:
        return guard

    membership = (
        UserRole.objects.filter(org_id=request.organization.org_id, user_id=user_id)
        .select_related("user")
        .first()
    )
    if membership is None:
        return Response({"detail": "User not found in organization."}, status=404)

    user = membership.user
    if not user.is_active or user.status != UserStatus.ACTIVE:
        user.is_active = True
        user.status = UserStatus.ACTIVE
        user.save(update_fields=["is_active", "status"])

    role = get_user_role(request.organization.org_id, user.id)
    serializer = OrganizationUserSerializer(build_user_payload(user, role))
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Invite organization user",
    description="Invite a user to the current organization (admin-only).",
    request=OrganizationInviteCreateSerializer,
    responses={201: OrganizationInviteResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite_user_view(request):
    """Invite a user to the current organization."""
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


@extend_schema(
    summary="Accept organization invite",
    description="Accept an organization invite using the invite token.",
    request=OrganizationInviteAcceptSerializer,
    responses={200: OrganizationInviteAcceptResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def accept_invite_view(request):
    """Accept an organization invite using the provided token and password."""
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
