from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from shared.logging import get_logger

from .serializers import UserCreateSerializer, UserResponseSerializer

logger = get_logger(__name__)
User = get_user_model()


@extend_schema(
    summary="Register user",
    description="Create a new user account.",
    request=UserCreateSerializer,
    responses={201: UserResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user_view(request):
    """Register a new user account."""
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = User(
        username=serializer.validated_data["username"],
        email=serializer.validated_data["email"],
        first_name=serializer.validated_data.get("first_name", ""),
        last_name=serializer.validated_data.get("last_name", ""),
    )
    user.set_password(serializer.validated_data["password"])
    user.save()

    logger.info("User registered", extra={"user_id": user.id})

    response_serializer = UserResponseSerializer(user)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
