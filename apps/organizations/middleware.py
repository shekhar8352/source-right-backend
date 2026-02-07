from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from apps.access_control.models import UserRole
from apps.access_control.domain.enums import RoleType
from apps.accounts.authentication import OrgTokenAuthentication

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


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
            token_auth = OrgTokenAuthentication()
            try:
                auth_result = token_auth.authenticate(request)
            except AuthenticationFailed as exc:
                return JsonResponse({"detail": str(exc.detail)}, status=401)
            if auth_result:
                request.user, request.auth = auth_result
            else:
                return JsonResponse(
                    {"detail": "Authentication credentials were not provided."}, status=401
                )

        token_org_id = getattr(request, "org_id", None)
        session_org_id = None
        if not token_org_id and hasattr(request, "session"):
            session_org_id = request.session.get("org_id")

        if token_org_id:
            org_id = token_org_id
        elif session_org_id:
            org_id = session_org_id
        else:
            org_id = _get_org_id_from_request(request)
        if not org_id:
            return JsonResponse({"detail": "Organization context is required."}, status=403)

        membership_role = None
        if getattr(request, "organization", None) is not None and request.org_id == org_id:
            membership_role = request.organization_role
        else:
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
            membership_role = membership.role

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
