from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema

from shared.logging import get_logger

from apps.organizations.models import Organization
from apps.access_control.repositories.user_role_repository import UserRoleRepository

from .serializers import (
    TokenResponseSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserResponseSerializer,
)

logger = get_logger(__name__)
User = get_user_model()


@extend_schema(
    summary="Register user",
    description=(
        "Create a new user account with a required primary role. "
        "ORG_ADMIN can be created without org_id."
    ),
    request=UserCreateSerializer,
    responses={201: UserResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user_view(request):
    """Register a new user account."""
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    org_id = serializer.validated_data.get("org_id")
    role = serializer.validated_data["role"]
    organization = None
    if org_id:
        try:
            organization = Organization.objects.get(org_id=org_id)
        except Organization.DoesNotExist:
            return Response({"detail": "Organization not found."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user = User(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            primary_role=role,
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )
        user.set_password(serializer.validated_data["password"])
        user.save()

        if organization:
            UserRoleRepository.assign_role(user=user, org=organization, role=role)

    logger.info("User registered", extra={"user_id": user.id})

    response_serializer = UserResponseSerializer(user)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Login",
    description="Authenticate a user and return an API token.",
    request=UserLoginSerializer,
    responses={200: TokenResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate a user and return an API token."""
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data.get("username")
    email = serializer.validated_data.get("email")
    password = serializer.validated_data["password"]

    if email and not username:
        user = User.objects.filter(email__iexact=email).first()
        username = user.username if user else None

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"detail": "User is inactive."}, status=status.HTTP_403_FORBIDDEN)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key}, status=status.HTTP_200_OK)
