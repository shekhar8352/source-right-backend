from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.access_control.domain.enums import RoleType
from apps.accounts.models import UserStatus
from apps.organizations.services.organization_service import create_organization
from apps.organizations.domain.enums import OrganizationStatus


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD"],
    ALLOWED_COUNTRIES=["US"],
)
class SoftDeleteTests(TestCase):
    def test_user_soft_delete(self):
        user = get_user_model().objects.create_user(
            username="inactive-user",
            email="inactive-user@example.com",
            password="pass1234",
            primary_role=RoleType.VIEWER,
        )

        user.delete()
        user.refresh_from_db()

        self.assertEqual(user.status, UserStatus.INACTIVE)
        self.assertFalse(user.is_active)
        self.assertTrue(get_user_model().objects.filter(id=user.id).exists())

    def test_organization_soft_delete(self):
        admin = get_user_model().objects.create_user(
            username="org-admin",
            email="org-admin@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        org = create_organization(
            creator=admin,
            name="Acme",
            country="US",
            base_currency="USD",
        )

        org.delete()
        org.refresh_from_db()

        self.assertEqual(org.status, OrganizationStatus.DELETED)
        self.assertTrue(type(org).objects.filter(org_id=org.org_id).exists())
