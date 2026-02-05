from django.db import models


class OrganizationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    DELETED = "DELETED", "Deleted"


class RoleType(models.TextChoices):
    ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
