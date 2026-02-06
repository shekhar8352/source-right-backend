from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.access_control.domain.enums import InviteStatus, RoleType
from apps.access_control.models import OrganizationInvite, UserRole
from apps.organizations.services.organization_service import create_organization


@override_settings(
    DEFAULT_BASE_CURRENCY="USD",
    ALLOWED_CURRENCIES=["USD", "INR"],
    ALLOWED_COUNTRIES=["US", "IN"],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@sourceright.local",
)
class OrganizationInviteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass1234",
            primary_role=RoleType.ORG_ADMIN,
        )
        self.client = APIClient()
        self.invite_url = "/api/organizations/invites"
        self.accept_url = "/api/organizations/invites/accept"

    def _login_as(self, user, password="pass1234"):
        self.client.logout()
        self.assertTrue(self.client.login(username=user.username, password=password))

    def test_admin_can_invite_user(self):
        self._login_as(self.user)
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )

        payload = {"email": "invitee@example.com", "role": RoleType.VIEWER}
        response = self.client.post(
            self.invite_url, payload, format="json", HTTP_X_ORG_ID=org.org_id
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "invitee@example.com")
        self.assertEqual(data["status"], InviteStatus.INVITED.value)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("invitee@example.com", mail.outbox[0].to)

    def test_non_admin_cannot_invite_user(self):
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )
        member = get_user_model().objects.create_user(
            username="member",
            email="member@example.com",
            password="pass1234",
            primary_role=RoleType.VIEWER,
        )
        UserRole.objects.create(user=member, org=org, role=RoleType.VIEWER)

        self._login_as(member)
        payload = {"email": "invitee@example.com", "role": RoleType.VIEWER}
        response = self.client.post(
            self.invite_url, payload, format="json", HTTP_X_ORG_ID=org.org_id
        )

        self.assertEqual(response.status_code, 403)

    def test_duplicate_email_invite_rejected(self):
        self._login_as(self.user)
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )

        payload = {"email": "invitee@example.com", "role": RoleType.VIEWER}
        first = self.client.post(
            self.invite_url, payload, format="json", HTTP_X_ORG_ID=org.org_id
        )
        second = self.client.post(
            self.invite_url, payload, format="json", HTTP_X_ORG_ID=org.org_id
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)

    def test_accept_invite_sets_active_and_creates_user(self):
        self._login_as(self.user)
        org = create_organization(
            creator=self.user, name="Org One", country="IN", base_currency="INR"
        )

        payload = {"email": "invitee@example.com", "role": RoleType.VIEWER}
        response = self.client.post(
            self.invite_url, payload, format="json", HTTP_X_ORG_ID=org.org_id
        )
        self.assertEqual(response.status_code, 201)

        invite = OrganizationInvite.objects.get(email="invitee@example.com")
        accept_payload = {"token": invite.token, "password": "StrongPass123"}
        accept_response = self.client.post(self.accept_url, accept_payload, format="json")

        self.assertEqual(accept_response.status_code, 200)
        invite.refresh_from_db()
        self.assertEqual(invite.status, InviteStatus.ACTIVE)
        self.assertIsNotNone(invite.accepted_at)
        self.assertTrue(
            UserRole.objects.filter(
                org=org,
                user__email="invitee@example.com",
                role=RoleType.VIEWER,
            ).exists()
        )
