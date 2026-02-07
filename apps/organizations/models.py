from __future__ import annotations

from django.conf import settings
from django.db import models

from .domain.enums import OrganizationStatus
from .domain.identifiers import generate_org_id


class OrganizationQuerySet(models.QuerySet):
    def delete(self):  # pragma: no cover - used for safety
        return self.update(status=OrganizationStatus.DELETED)


class Organization(models.Model):
    org_id = models.CharField(
        primary_key=True,
        max_length=40,
        editable=False,
        default=generate_org_id,
    )
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=3)
    base_currency = models.CharField(max_length=3)
    timezone = models.CharField(max_length=64, default="UTC")
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
    )

    objects = OrganizationQuerySet.as_manager()

    class Meta:
        db_table = "organizations"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.name} ({self.org_id})"

    def soft_delete(self) -> None:
        if self.status != OrganizationStatus.DELETED:
            self.status = OrganizationStatus.DELETED
            self.save(update_fields=["status"])

    def delete(self, using=None, keep_parents=False):  # pragma: no cover - safety
        self.soft_delete()
        return (1, {self._meta.label: 1})
