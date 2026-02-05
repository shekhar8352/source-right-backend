from __future__ import annotations

from django.db import transaction

from ..domain.enums import RoleType
from ..repositories.organization_repository import OrganizationRepository
from ..repositories.user_role_repository import UserRoleRepository


def create_organization(*, creator, name: str, country: str, base_currency: str):
    """Create an organization and assign ORG_ADMIN to the creator atomically."""
    with transaction.atomic():
        organization = OrganizationRepository.create(
            name=name,
            country=country,
            base_currency=base_currency,
            created_by=creator,
        )
        UserRoleRepository.assign_role(
            user=creator,
            org=organization,
            role=RoleType.ORG_ADMIN,
        )
    return organization
