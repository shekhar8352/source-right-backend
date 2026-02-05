from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organizations.domain.enums import RoleType
from apps.organizations.models import Organization, UserRole
from apps.organizations.repositories.user_role_repository import UserRoleRepository
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD", "INR"],
    ALLOWED_COUNTRIES=["US", "IN"],
)
class OrganizationCreationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin", email="admin@example.com", password="pass1234"
        )
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)
        self.url = reverse("create-organization")

    def test_create_organization_success(self):
        payload = {"name": "Acme Corp", "country": "IN", "base_currency": "INR"}

        response = self.api_client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Acme Corp")
        self.assertEqual(data["country"], "IN")
        self.assertEqual(data["base_currency"], "INR")
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
        payload = {"name": "   ", "country": "IN", "base_currency": "INR"}

        response = self.api_client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)

    def test_duplicate_name_allowed(self):
        payload = {"name": "Acme Corp", "country": "IN", "base_currency": "INR"}

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
