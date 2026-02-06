from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.access_control.models import UserRole

from .services.auth_token_service import parse_token

User = get_user_model()


class OrgTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"
    alt_keyword = "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None

        try:
            auth_keyword = auth[0].decode()
        except UnicodeError as exc:
            raise AuthenticationFailed("Invalid token header.") from exc

        if auth_keyword not in {self.keyword, self.alt_keyword}:
            return None

        if len(auth) != 2:
            raise AuthenticationFailed("Invalid token header.")

        try:
            token = auth[1].decode()
        except UnicodeError as exc:
            raise AuthenticationFailed("Invalid token header.") from exc

        payload = self._decode_token(token)
        user = self._get_user(payload)

        org_id = payload["org_id"]
        role = payload["role"]

        if getattr(request, "organization", None) is not None:
            if org_id != request.organization.org_id:
                raise AuthenticationFailed("Token org context does not match request.")
            if role != request.organization_role:
                raise AuthenticationFailed("Token role does not match request.")
            return (user, payload)

        membership = (
            UserRole.objects.select_related("org")
            .filter(user=user, org_id=org_id)
            .first()
        )
        if membership is None:
            raise AuthenticationFailed("Token org context is invalid.")
        if membership.role != role:
            raise AuthenticationFailed("Token role is invalid.")

        request.org_id = org_id
        request.organization = membership.org
        request.organization_role = membership.role

        return (user, payload)

    def _decode_token(self, token: str) -> dict:
        try:
            payload = parse_token(token)
        except signing.SignatureExpired as exc:
            raise AuthenticationFailed("Token has expired.") from exc
        except signing.BadSignature as exc:
            raise AuthenticationFailed("Invalid token.") from exc

        if not isinstance(payload, dict):
            raise AuthenticationFailed("Invalid token.")

        if not payload.get("org_id") or not payload.get("role") or not payload.get("user_id"):
            raise AuthenticationFailed("Token missing org context.")

        return payload

    def _get_user(self, payload: dict):
        user_id = payload["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found.") from exc
        if not user.is_active:
            raise AuthenticationFailed("User is inactive.")
        return user
