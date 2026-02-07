from __future__ import annotations

from typing import Optional

from django.db import IntegrityError

from ..models import Organization


class OrganizationRepository:
    @staticmethod
    def create(
        *, name: str, country: str, base_currency: str, created_by, timezone: str = "UTC"
    ) -> Organization:
        """Create organization with a retry on org_id collision."""
        attempts = 0
        while True:
            try:
                return Organization.objects.create(
                    name=name,
                    country=country,
                    base_currency=base_currency,
                    timezone=timezone,
                    created_by=created_by,
                )
            except IntegrityError:  # pragma: no cover - extremely unlikely
                attempts += 1
                if attempts >= 3:
                    raise

    @staticmethod
    def get_by_org_id(org_id: str) -> Optional[Organization]:
        return Organization.objects.filter(org_id=org_id).first()
