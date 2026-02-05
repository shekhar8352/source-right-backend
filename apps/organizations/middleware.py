from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.http import JsonResponse

from apps.access_control.models import UserRole


def _normalize_path(path: str) -> str:
    if path != "/" and path.endswith("/"):
        return path.rstrip("/")
    return path


def _get_org_id_from_request(request) -> str | None:
    header_name = getattr(settings, "ORG_CONTEXT_HEADER", "X-Org-Id")
    meta_key = f"HTTP_{header_name.upper().replace('-', '_')}"
    return request.META.get(meta_key)


def _matches_prefix(path: str, prefixes: Iterable[str]) -> bool:
    for prefix in prefixes:
        if path.startswith(prefix):
            return True
    return False


def _is_exempt(path: str, exemptions: Iterable[str]) -> bool:
    normalized_path = _normalize_path(path)
    for exempt in exemptions:
        if normalized_path == _normalize_path(exempt):
            return True
    return False


class OrganizationContextMiddleware:
    """Enforce org context for API requests to prevent cross-tenant access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_enforce(request):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return JsonResponse(
                {"detail": "Authentication credentials were not provided."}, status=401
            )

        org_id = _get_org_id_from_request(request)
        if not org_id:
            return JsonResponse({"detail": "Organization context is required."}, status=403)

        membership = (
            UserRole.objects.select_related("org")
            .filter(user=request.user, org_id=org_id)
            .first()
        )
        if membership is None:
            return JsonResponse(
                {"detail": "User does not belong to the specified organization."},
                status=403,
            )

        request.org_id = org_id
        request.organization = membership.org
        request.organization_role = membership.role

        return self.get_response(request)

    def _should_enforce(self, request) -> bool:
        path = request.path
        enforced_prefixes = getattr(settings, "ORG_CONTEXT_ENFORCED_PREFIXES", ["/api/"])
        exempt_paths = getattr(settings, "ORG_CONTEXT_EXEMPT_PATHS", [])

        if not _matches_prefix(path, enforced_prefixes):
            return False
        if _is_exempt(path, exempt_paths):
            return False
        return True
