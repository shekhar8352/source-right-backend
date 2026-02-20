from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.access_control.domain.enums import RoleType
from apps.access_control.repositories.user_role_repository import UserRoleRepository
from apps.accounts.services.auth_token_service import issue_token
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD"], 
    ALLOWED_COUNTRIES=["US"],
)
class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "pass1234"

        self.org_admin = self._create_user("admin", RoleType.ORG_ADMIN)
        self.org = create_organization(
            creator=self.org_admin,
            name="SourceRight",
            country="US",
            base_currency="USD",
        )

        self.finance = self._create_user("finance", RoleType.FINANCE)
        self.approver = self._create_user("approver", RoleType.APPROVER)
        self.viewer = self._create_user("viewer", RoleType.VIEWER)
        self.vendor = self._create_user("vendor", RoleType.VENDOR)

        for user, role in [
            (self.finance, RoleType.FINANCE),
            (self.approver, RoleType.APPROVER),
            (self.viewer, RoleType.VIEWER),
            (self.vendor, RoleType.VENDOR),
        ]:
            UserRoleRepository.assign_role(user=user, org=self.org, role=role)

    def _create_user(self, username: str, role: RoleType):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=self.password,
            primary_role=role,
        )

    def _auth_headers(self, user):
        token = issue_token(user_id=user.id, org_id=self.org.org_id, role=user.primary_role)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_create_vendor_permissions(self):
        url = "/api/internal/vendors"
        payload = {"name": "Acme"}

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.org_admin))
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.finance))
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.approver))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.viewer))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.vendor))
        self.assertEqual(response.status_code, 403)

    def test_approve_invoice_permissions(self):
        url = "/api/internal/invoices/inv-123/approve"

        response = self.client.post(url, {}, format="json", **self._auth_headers(self.approver))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {}, format="json", **self._auth_headers(self.org_admin))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, {}, format="json", **self._auth_headers(self.finance))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, {}, format="json", **self._auth_headers(self.viewer))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, {}, format="json", **self._auth_headers(self.vendor))
        self.assertEqual(response.status_code, 403)

    def test_view_invoice_permissions(self):
        url = "/api/internal/invoices"

        response = self.client.get(url, **self._auth_headers(self.org_admin))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, **self._auth_headers(self.finance))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, **self._auth_headers(self.approver))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, **self._auth_headers(self.viewer))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, **self._auth_headers(self.vendor))
        self.assertEqual(response.status_code, 403)

    def test_upload_invoice_permissions(self):
        url = "/api/vendor/invoices/upload"
        payload = {"invoice_id": "inv-001", "amount": 1200}

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.vendor))
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.org_admin))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.finance))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.approver))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url, payload, format="json", **self._auth_headers(self.viewer))
        self.assertEqual(response.status_code, 403)
