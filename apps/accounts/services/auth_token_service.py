from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _build_refresh_token(*, user, org_id: str, role: str) -> RefreshToken:
    refresh = RefreshToken.for_user(user)
    refresh["org_id"] = org_id
    refresh["role"] = role
    return refresh


def issue_token(*, user_id: int, org_id: str, role: str) -> str:
    """
    Backward-compatible helper that returns an access token string.
    """
    user = User.objects.get(id=user_id)
    refresh = _build_refresh_token(user=user, org_id=org_id, role=role)
    return str(refresh.access_token)


def issue_token_pair(*, user_id: int, org_id: str, role: str) -> dict[str, str]:
    user = User.objects.get(id=user_id)
    refresh = _build_refresh_token(user=user, org_id=org_id, role=role)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }
