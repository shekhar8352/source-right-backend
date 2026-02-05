from __future__ import annotations

from typing import Optional

from apps.organizations.models import Organization

from ..models import OrganizationInvite


class OrganizationInviteRepository:
    @staticmethod
    def create(*, org: Organization, email: str, role: str, token: str, invited_by):
        return OrganizationInvite.objects.create(
            org=org,
            email=email,
            role=role,
            token=token,
            invited_by=invited_by,
        )

    @staticmethod
    def get_by_token(token: str) -> Optional[OrganizationInvite]:
        return OrganizationInvite.objects.filter(token=token).select_related("org").first()

    @staticmethod
    def list_for_org(org_id: str):
        return OrganizationInvite.objects.filter(org_id=org_id)
