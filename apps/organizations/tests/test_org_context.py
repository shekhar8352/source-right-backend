from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

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

    def _auth_headers(self, *, user, org_id, role):
        token = issue_token(user_id=user.id, org_id=org_id, role=role)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_missing_auth_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_missing_org_context_rejected(self):
        token = str(AccessToken.for_user(self.user))

        response = self.client.get(self.url, HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, 401)

    def test_invalid_org_context_rejected(self):
        headers = self._auth_headers(
            user=self.user,
            org_id="org_fake",
            role=RoleType.ORG_ADMIN,
        )

        response = self.client.get(self.url, **headers)

        self.assertEqual(response.status_code, 401)

    def test_valid_org_context_allows_request(self):
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        headers = self._auth_headers(
            user=self.user,
            org_id=org.org_id,
            role=RoleType.ORG_ADMIN,
        )

        response = self.client.get(self.url, **headers)

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
        headers = self._auth_headers(
            user=self.user,
            org_id=org.org_id,
            role=RoleType.ORG_ADMIN,
        )

        response = self.client.get(
            "/api/internal/invoices",
            **headers,
            HTTP_X_ORG_ID=other_org.org_id,
        )

        self.assertEqual(response.status_code, 200)

    def test_token_role_mismatch_is_rejected(self):
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        headers = self._auth_headers(
            user=self.user,
            org_id=org.org_id,
            role=RoleType.FINANCE,
        )
        response = self.client.get("/api/internal/invoices", **headers)

        self.assertEqual(response.status_code, 401)
