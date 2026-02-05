from __future__ import annotations

from apps.organizations.models import Organization

from ..domain.enums import RoleType
from ..models import UserRole


class UserRoleRepository:
    @staticmethod
    def assign_role(*, user, org: Organization, role: RoleType) -> UserRole:
        return UserRole.objects.create(user=user, org=org, role=role)

    @staticmethod
    def list_for_org(org_id: str):
        return UserRole.objects.for_org(org_id)
