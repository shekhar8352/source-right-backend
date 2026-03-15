from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .serializers import MeOrganizationSerializer, MeResponseSerializer, MeUserSerializer


@extend_schema(
    summary="Current user and organization",
    description=(
        "Returns the authenticated user and their current organization. "
        "Call after login to hydrate Redux/store. "
        "Organization and role are null when using a setup token (e.g. before creating an org)."
    ),
    responses={200: MeResponseSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return current user and organization for dashboard / Redux."""
    user = request.user
    organization = getattr(request, "organization", None)
    role = getattr(request, "organization_role", None)

    user_data = MeUserSerializer(user).data
    org_data = MeOrganizationSerializer(organization).data if organization else None

    payload = {
        "user": user_data,
        "organization": org_data,
        "role": role,
    }
    serializer = MeResponseSerializer(payload)
    return Response(serializer.data, status=status.HTTP_200_OK)
