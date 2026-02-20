import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from apps.access_control.domain.enums import RoleType
from apps.organizations.services.organization_service import create_organization
from apps.accounts.services.auth_token_service import issue_token


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
        self.assertTrue(payload["access_token"])
        self.assertTrue(payload["refresh_token"])

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
        token = str(AccessToken.for_user(self.user))

        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 401)

    def test_token_expiry_is_enforced(self):
        token = AccessToken.for_user(self.user)
        token["org_id"] = self.org.org_id
        token["role"] = RoleType.ORG_ADMIN
        token.set_exp(lifetime=timedelta(seconds=1))

        time.sleep(1.1)
        response = self.client.get(
            "/api/internal/invoices",
            HTTP_AUTHORIZATION=f"Bearer {str(token)}",
        )

        self.assertEqual(response.status_code, 401)

    def test_refresh_token_returns_new_access_token(self):
        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        refresh = response.json()["refresh_token"]

        refresh_response = self.client.post(
            "/api/accounts/token/refresh",
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, 200)
        payload = refresh_response.json()
        self.assertIn("access", payload)

    def test_refresh_token_is_persisted_in_db(self):
        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        refresh = response.json()["refresh_token"]
        refresh_obj = RefreshToken(refresh)

        self.assertTrue(
            OutstandingToken.objects.filter(
                jti=str(refresh_obj["jti"]),
                user=self.user,
            ).exists()
        )

    def test_logout_blacklists_refresh_token(self):
        response = self.client.post(
            "/api/accounts/login",
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        refresh = response.json()["refresh_token"]

        logout_response = self.client.post(
            "/api/accounts/logout",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout_response.status_code, 200)

        refresh_response = self.client.post(
            "/api/accounts/token/refresh",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)
