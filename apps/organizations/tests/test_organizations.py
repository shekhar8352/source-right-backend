from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.access_control.domain.enums import RoleType
from apps.access_control.models import UserRole
from apps.access_control.repositories.user_role_repository import UserRoleRepository
from apps.accounts.services.auth_token_service import issue_token
from apps.organizations.models import Organization
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD", "INR"],
    ALLOWED_COUNTRIES=["US", "IN"],
)
class OrganizationCreationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        self.api_client = APIClient()
        self.url = reverse("create-organization")

    def test_create_organization_success(self):
        payload = {
            "name": "Acme Corp",
            "country": "IN",
            "base_currency": "INR",
            "created_by_id": self.user.id,
        }

        response = self.api_client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Acme Corp")
        self.assertEqual(data["country"], "IN")
        self.assertEqual(data["base_currency"], "INR")
        self.assertEqual(data["timezone"], "UTC")
        self.assertEqual(data["status"], "ACTIVE")
        self.assertIn("org_id", data)
        self.assertIn("created_at", data)

        organization = Organization.objects.get(org_id=data["org_id"])
        self.assertTrue(
            UserRole.objects.filter(
                user=self.user,
                org=organization,
                role=RoleType.ORG_ADMIN,
            ).exists()
        )

    def test_empty_name_rejected(self):
        payload = {
            "name": "   ",
            "country": "IN",
            "base_currency": "INR",
            "created_by_id": self.user.id,
        }

        response = self.api_client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)

    def test_duplicate_name_allowed(self):
        payload = {
            "name": "Acme Corp",
            "country": "IN",
            "base_currency": "INR",
            "created_by_id": self.user.id,
        }

        first = self.api_client.post(self.url, payload, format="json")
        second = self.api_client.post(self.url, payload, format="json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.json()["org_id"], second.json()["org_id"])

    def test_cross_org_isolation_scoped_queries(self):
        org_one = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        org_two = create_organization(
            creator=self.user, name="Org Two", country="US", base_currency="USD"
        )

        roles_for_org_one = UserRoleRepository.list_for_org(org_one.org_id)

        self.assertEqual(roles_for_org_one.count(), 1)
        self.assertEqual(roles_for_org_one.first().org_id, org_one.org_id)
        self.assertNotEqual(roles_for_org_one.first().org_id, org_two.org_id)


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD", "INR"],
    ALLOWED_COUNTRIES=["US", "IN"],
)
class OrganizationSettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "pass1234"
        self.admin = get_user_model().objects.create_user(
            username="org-admin",
            email="org-admin@example.com",
            password=self.password,
            primary_role=RoleType.ORG_ADMIN,
        )
        self.org = create_organization(
            creator=self.admin,
            name="Acme",
            country="US",
            base_currency="USD",
        )
        self.settings_url = reverse("organization-settings")

    def _auth_headers(self, user, role):
        token = issue_token(user_id=user.id, org_id=self.org.org_id, role=role)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_admin_can_update_settings(self):
        response = self.client.patch(
            self.settings_url,
            {"base_currency": "INR", "country": "IN", "timezone": "Asia/Kolkata"},
            format="json",
            **self._auth_headers(self.admin, RoleType.ORG_ADMIN),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["org_id"], self.org.org_id)
        self.assertEqual(payload["base_currency"], "INR")
        self.assertEqual(payload["country"], "IN")
        self.assertEqual(payload["timezone"], "Asia/Kolkata")

        self.org.refresh_from_db()
        self.assertEqual(self.org.base_currency, "INR")
        self.assertEqual(self.org.country, "IN")
        self.assertEqual(self.org.timezone, "Asia/Kolkata")

    def test_non_admin_cannot_update_settings(self):
        finance = get_user_model().objects.create_user(
            username="finance-user",
            email="finance-user@example.com",
            password=self.password,
            primary_role=RoleType.FINANCE,
        )
        UserRoleRepository.assign_role(user=finance, org=self.org, role=RoleType.FINANCE)

        response = self.client.patch(
            self.settings_url,
            {"base_currency": "INR"},
            format="json",
            **self._auth_headers(finance, RoleType.FINANCE),
        )

        self.assertEqual(response.status_code, 403)

    def test_updated_settings_apply_to_new_records(self):
        self.client.patch(
            self.settings_url,
            {"base_currency": "INR", "country": "IN", "timezone": "Asia/Kolkata"},
            format="json",
            **self._auth_headers(self.admin, RoleType.ORG_ADMIN),
        )

        vendor_response = self.client.post(
            "/api/internal/vendors",
            {"name": "Vendor One"},
            format="json",
            **self._auth_headers(self.admin, RoleType.ORG_ADMIN),
        )
        self.assertEqual(vendor_response.status_code, 201)
        vendor_payload = vendor_response.json()
        self.assertEqual(vendor_payload["country"], "IN")
        self.assertEqual(vendor_payload["timezone"], "Asia/Kolkata")

        vendor_user = get_user_model().objects.create_user(
            username="vendor-user",
            email="vendor-user@example.com",
            password=self.password,
            primary_role=RoleType.VENDOR,
        )
        UserRoleRepository.assign_role(user=vendor_user, org=self.org, role=RoleType.VENDOR)

        invoice_response = self.client.post(
            "/api/vendor/invoices/upload",
            {"invoice_id": "inv-999", "amount": 500},
            format="json",
            **self._auth_headers(vendor_user, RoleType.VENDOR),
        )
        self.assertEqual(invoice_response.status_code, 201)
        invoice_payload = invoice_response.json()
        self.assertEqual(invoice_payload["currency"], "INR")
        self.assertEqual(invoice_payload["country"], "IN")
        self.assertEqual(invoice_payload["timezone"], "Asia/Kolkata")
