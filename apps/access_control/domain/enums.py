from django.db import models


class RoleType(models.TextChoices):
    ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
    FINANCE = "FINANCE", "Finance"
    APPROVER = "APPROVER", "Approver"
    VIEWER = "VIEWER", "Viewer"
    VENDOR = "VENDOR", "Vendor"


class InviteStatus(models.TextChoices):
    INVITED = "INVITED", "Invited"
    ACTIVE = "ACTIVE", "Active"
