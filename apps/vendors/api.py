from uuid import uuid4

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.access_control.domain.enums import RoleType
from apps.access_control.permissions import require_roles

from .serializers import VendorCreateSerializer, VendorResponseSerializer


@extend_schema(
    summary="Create vendor",
    description="Create a vendor (internal only).",
    request=VendorCreateSerializer,
    responses={201: VendorResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_vendor_view(request):
    """Create a vendor (internal only)."""
    guard = require_roles(
        request,
        [RoleType.ORG_ADMIN, RoleType.FINANCE],
        action="create vendors",
    )
    if guard:
        return guard

    serializer = VendorCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    vendor_id = f"ven_{uuid4().hex[:10]}"
    payload = {"vendor_id": vendor_id, "name": serializer.validated_data["name"]}
    return Response(payload, status=status.HTTP_201_CREATED)
