from django.db import models


class OrganizationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    DELETED = "DELETED", "Deleted"


class RoleType(models.TextChoices):
    ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
    ORG_MEMBER = "ORG_MEMBER", "Organization Member"


class InviteStatus(models.TextChoices):
    INVITED = "INVITED", "Invited"
    ACTIVE = "ACTIVE", "Active"
