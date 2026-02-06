from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

from apps.access_control.domain.enums import RoleType
from apps.access_control.models import UserRole

User = get_user_model()


def require_org_admin(request):
    if getattr(request, "organization", None) is None:
        return Response(
            {"detail": "Organization context is required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if getattr(request, "organization_role", None) != RoleType.ORG_ADMIN:
        return Response(
            {"detail": "Only organization admins can perform this action."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def build_user_payload(user, role):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "role": role,
    }


def get_user_role(org_id: str, user_id: int) -> str | None:
    return (
        UserRole.objects.filter(org_id=org_id, user_id=user_id)
        .values_list("role", flat=True)
        .first()
    )


def is_last_active_admin(org_id: str, user_id: int) -> bool:
    active_admins = UserRole.objects.filter(
        org_id=org_id, role=RoleType.ORG_ADMIN, user__is_active=True
    )
    return active_admins.count() == 1 and active_admins.filter(user_id=user_id).exists()
