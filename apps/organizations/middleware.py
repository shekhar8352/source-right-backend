from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from apps.access_control.domain.enums import RoleType
from apps.accounts.authentication import OrgTokenAuthentication

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _normalize_path(path: str) -> str:
    if path != "/" and path.endswith("/"):
        return path.rstrip("/")
    return path


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

        token_auth = OrgTokenAuthentication()
        try:
            auth_result = token_auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({"detail": str(exc.detail)}, status=401)
        if not auth_result:
            return JsonResponse(
                {"detail": "Authentication credentials were not provided."},
                status=401,
            )
        request.user, request.auth = auth_result
        membership_role = request.organization_role

        if self._is_internal(request.path) and membership_role == RoleType.VENDOR:
            return JsonResponse(
                {"detail": "Vendor role cannot access internal APIs."},
                status=403,
            )

        if membership_role == RoleType.VIEWER and request.method not in SAFE_METHODS:
            return JsonResponse(
                {"detail": "Viewer role cannot mutate data."},
                status=403,
            )

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

    def _is_internal(self, path: str) -> bool:
        internal_prefixes = getattr(settings, "INTERNAL_API_PREFIXES", ["/api/internal/"])
        return _matches_prefix(path, internal_prefixes)
