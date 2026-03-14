from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.access_control.domain.enums import RoleType
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD"],
    ALLOWED_COUNTRIES=["US"],
)
class RegisterWithOrgTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_with_org_id_returns_tokens(self):
        """Register with existing org_id returns tokens immediately."""
        admin = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass",
            primary_role=RoleType.ORG_ADMIN,
        )
        org = create_organization(
            creator=admin,
            name="Existing Org",
            country="US",
            base_currency="USD",
        )

        response = self.client.post(
            "/api/accounts/register",
            {
                "username": "finance",
                "email": "finance@example.com",
                "password": "SecurePass123!",
                "role": RoleType.FINANCE,
                "org_id": org.org_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("access_token", payload)
        self.assertEqual(payload["org_id"], org.org_id)
        self.assertEqual(payload["role"], RoleType.FINANCE)

    def test_register_org_admin_with_org_id_returns_tokens(self):
        """Register ORG_ADMIN with existing org_id returns tokens immediately."""
        admin = get_user_model().objects.create_user(
            username="creator",
            email="creator@example.com",
            password="pass",
            primary_role=RoleType.ORG_ADMIN,
        )
        org = create_organization(
            creator=admin,
            name="Acme Corp",
            country="US",
            base_currency="USD",
        )

        response = self.client.post(
            "/api/accounts/register",
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePass123!",
                "role": RoleType.ORG_ADMIN,
                "org_id": org.org_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["username"], "admin")
        self.assertEqual(payload["primary_role"], RoleType.ORG_ADMIN)
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)
        self.assertIn("org_id", payload)
        self.assertEqual(payload["role"], RoleType.ORG_ADMIN)

        # Token should work for protected endpoints
        access = payload["access_token"]
        get_response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(get_response.status_code, 200)

    def test_register_org_admin_without_org_returns_setup_tokens(self):
        """Register ORG_ADMIN without org returns setup tokens (no org_id); create org separately."""
        response = self.client.post(
            "/api/accounts/register",
            {
                "username": "admin2",
                "email": "admin2@example.com",
                "password": "SecurePass123!",
                "role": RoleType.ORG_ADMIN,
                "first_name": "Admin",
                "last_name": "User",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["username"], "admin2")
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)
        self.assertNotIn("org_id", payload)
        self.assertNotIn("role", payload)
