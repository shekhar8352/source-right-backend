from __future__ import annotations

from collections.abc import Iterable

from rest_framework import status
from rest_framework.response import Response

from .domain.enums import RoleType

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _normalize_roles(roles: Iterable[RoleType | str]) -> set[str]:
    normalized: set[str] = set()
    for role in roles:
        if isinstance(role, RoleType):
            normalized.add(role.value)
        else:
            normalized.add(str(role))
    return normalized


def require_roles(request, allowed_roles: Iterable[RoleType | str], *, action: str | None = None):
    if getattr(request, "organization", None) is None:
        return Response(
            {"detail": "Organization context is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    role = getattr(request, "organization_role", None)
    if role is None:
        return Response(
            {"detail": "Organization role is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if role == RoleType.VIEWER and request.method not in SAFE_METHODS:
        return Response(
            {"detail": "Viewer role cannot mutate data."},
            status=status.HTTP_403_FORBIDDEN,
        )

    normalized_roles = _normalize_roles(allowed_roles)
    if role not in normalized_roles:
        detail = (
            f"Role {role} is not allowed to {action}."
            if action
            else "You do not have permission to perform this action."
        )
        return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)

    return None
