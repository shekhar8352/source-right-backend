from __future__ import annotations

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.access_control.models import UserRole
from apps.accounts.models import UserStatus

class OrgTokenAuthentication(JWTAuthentication):

    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result is None:
            return None

        user, validated_token = auth_result
        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise AuthenticationFailed("User is inactive.")

        org_id = validated_token.get("org_id")
        role = validated_token.get("role")
        if not org_id or not role:
            raise AuthenticationFailed("Token missing org context.")

        # When middleware has already resolved org context, enforce claim consistency.
        if getattr(request, "organization", None) is not None:
            if org_id != request.organization.org_id:
                raise AuthenticationFailed("Token org context does not match request.")
            if role != request.organization_role:
                raise AuthenticationFailed("Token role does not match request.")
            return (user, validated_token)

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

        return (user, validated_token)
