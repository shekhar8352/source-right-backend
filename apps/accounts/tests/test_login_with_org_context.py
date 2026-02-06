import time

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.access_control.domain.enums import RoleType
from apps.organizations.services.organization_service import create_organization
from apps.accounts.services.auth_token_service import TOKEN_SALT, issue_token


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD"],
    ALLOWED_COUNTRIES=["US"],
)
class LoginWithOrgContextTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "pass1234"
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password=self.password,
            primary_role=RoleType.ORG_ADMIN,
        )
        self.org = create_organization(
            creator=self.user,
            name="SourceRight",
            country="US",
            base_currency="USD",
        )

    def test_login_returns_org_context(self):
        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["org_id"], self.org.org_id)
        self.assertEqual(payload["role"], RoleType.ORG_ADMIN)
        self.assertTrue(payload["token"])

    def test_login_requires_org_id_when_multiple_memberships(self):
        create_organization(
            creator=self.user,
            name="Second Org",
            country="US",
            base_currency="USD",
        )

        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_token_org_context_allows_request_without_header(self):
        token = issue_token(
            user_id=self.user.id,
            org_id=self.org.org_id,
            role=RoleType.ORG_ADMIN,
        )

        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)

    def test_token_without_org_context_is_rejected(self):
        token = signing.dumps({"user_id": self.user.id}, salt=TOKEN_SALT)

        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(AUTH_TOKEN_TTL_SECONDS=1)
    def test_token_expiry_is_enforced(self):
        token = issue_token(
            user_id=self.user.id,
            org_id=self.org.org_id,
            role=RoleType.ORG_ADMIN,
        )

        time.sleep(1.1)
        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 401)
