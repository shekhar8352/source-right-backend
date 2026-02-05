from __future__ import annotations

from django.conf import settings
from django.db import models

from .domain.enums import InviteStatus, OrganizationStatus, RoleType
from .domain.identifiers import generate_org_id


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

    class Meta:
        db_table = "organizations"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.name} ({self.org_id})"


class OrganizationScopedQuerySet(models.QuerySet):
    def for_org(self, org_id: str) -> "OrganizationScopedQuerySet":
        return self.filter(org_id=org_id)


class OrganizationScopedManager(models.Manager.from_queryset(OrganizationScopedQuerySet)):
    pass


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_roles",
    )
    org = models.ForeignKey(
        Organization,
        to_field="org_id",
        db_column="org_id",
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.CharField(max_length=40, choices=RoleType.choices)
    assigned_at = models.DateTimeField(auto_now_add=True)

    objects = OrganizationScopedManager()

    class Meta:
        db_table = "user_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "org", "role"],
                name="uniq_user_org_role",
            )
        ]
        indexes = [
            models.Index(fields=["org", "user"], name="idx_user_roles_org_user"),
            models.Index(fields=["org", "role"], name="idx_user_roles_org_role"),
        ]

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.user_id} -> {self.org_id} ({self.role})"


class OrganizationInvite(models.Model):
    org = models.ForeignKey(
        Organization,
        to_field="org_id",
        db_column="org_id",
        on_delete=models.CASCADE,
        related_name="invites",
    )
    email = models.EmailField()
    role = models.CharField(max_length=40, choices=RoleType.choices)
    status = models.CharField(
        max_length=20,
        choices=InviteStatus.choices,
        default=InviteStatus.INVITED,
    )
    token = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_organization_invites",
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accepted_organization_invites",
    )

    class Meta:
        db_table = "organization_invites"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "email"],
                name="uniq_org_invite_email",
            )
        ]
        indexes = [
            models.Index(fields=["org", "status"], name="idx_invites_org_status"),
            models.Index(fields=["email"], name="idx_invites_email"),
        ]

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.email} -> {self.org_id} ({self.status})"
