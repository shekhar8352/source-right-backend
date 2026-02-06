from __future__ import annotations

from django.conf import settings
from django.core import signing

TOKEN_SALT = "accounts.auth.token"


def issue_token(*, user_id: int, org_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "role": role,
    }
    return signing.dumps(payload, salt=TOKEN_SALT)


def parse_token(token: str) -> dict:
    max_age = getattr(settings, "AUTH_TOKEN_TTL_SECONDS", 3600)
    return signing.loads(token, salt=TOKEN_SALT, max_age=max_age)
