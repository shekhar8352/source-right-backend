from __future__ import annotations

from apps.organizations.models import Organization

from ..domain.enums import RoleType
from ..models import UserRole


class UserRoleRepository:
    @staticmethod
    def assign_role(*, user, org: Organization, role: RoleType) -> UserRole:
        user_role, _ = UserRole.objects.update_or_create(
            user=user,
            org=org,
            defaults={"role": role},
        )
        return user_role

    @staticmethod
    def list_for_org(org_id: str):
        return UserRole.objects.for_org(org_id)
