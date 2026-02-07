from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.access_control.domain.enums import RoleType
from apps.accounts.services.auth_token_service import issue_token
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD", "INR"],
    ALLOWED_COUNTRIES=["US", "IN"],
)
class OrganizationContextMiddlewareTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        self.client = APIClient()
        self.url = "/api/example"

    def test_missing_auth_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_missing_org_context_rejected(self):
        self.assertTrue(self.client.login(username="admin", password="pass1234"))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_invalid_org_context_rejected(self):
        self.assertTrue(self.client.login(username="admin", password="pass1234"))

        response = self.client.get(self.url, HTTP_X_ORG_ID="org_fake")

        self.assertEqual(response.status_code, 403)

    def test_valid_org_context_allows_request(self):
        self.assertTrue(self.client.login(username="admin", password="pass1234"))
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )

        response = self.client.get(self.url, HTTP_X_ORG_ID=org.org_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_token_org_context_ignores_header(self):
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        other_user = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        other_org = create_organization(
            creator=other_user, name="Org Two", country="US", base_currency="USD"
        )
        token = issue_token(
            user_id=self.user.id,
            org_id=org.org_id,
            role=RoleType.ORG_ADMIN,
        )

        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_ORG_ID=other_org.org_id,
        )

        self.assertEqual(response.status_code, 200)

    def test_session_org_context_ignores_header(self):
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        other_user = get_user_model().objects.create_user(
            username="other3",
            email="other3@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        other_org = create_organization(
            creator=other_user, name="Org Two", country="US", base_currency="USD"
        )

        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": "pass1234",
                "org_id": org.org_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/internal/invoices", HTTP_X_ORG_ID=other_org.org_id)

        self.assertEqual(response.status_code, 200)

    def test_cross_org_header_rejected_for_session_auth(self):
        create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        other_user = get_user_model().objects.create_user(
            username="other2",
            email="other2@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        other_org = create_organization(
            creator=other_user, name="Org Two", country="US", base_currency="USD"
        )

        self.assertTrue(self.client.login(username="admin", password="pass1234"))
        response = self.client.get("/api/internal/invoices", HTTP_X_ORG_ID=other_org.org_id)

        self.assertEqual(response.status_code, 403)
