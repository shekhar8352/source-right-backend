from __future__ import annotations

import re
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.services.email_service import send_email

from ..domain.enums import InviteStatus
from ..models import OrganizationInvite, UserRole
from ..repositories.invite_repository import OrganizationInviteRepository


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _base_username_from_email(email: str) -> str:
    prefix = email.split("@")[0]
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", prefix).strip("_")
    return cleaned or "user"


def _generate_unique_username(user_model, base: str) -> str:
    candidate = base
    counter = 1
    while user_model.objects.filter(username=candidate).exists():
        candidate = f"{base}{counter}"
        counter += 1
    return candidate


def _build_invite_link(token: str) -> str | None:
    base = getattr(settings, "INVITE_ACCEPT_URL_BASE", "").strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/?token={token}"


def send_invite_email(*, email: str, org_name: str, token: str) -> None:
    subject = f"You're invited to {org_name}"
    link = _build_invite_link(token)
    if link:
        message = (
            f"You've been invited to join {org_name}. "
            f"Accept your invite here: {link}"
        )
    else:
        message = (
            f"You've been invited to join {org_name}. "
            f"Use this invite token to accept: {token}"
        )
    send_email(subject=subject, message=message, recipients=[email])


def invite_user(*, org, email: str, role: str, invited_by) -> OrganizationInvite:
    normalized_email = _normalize_email(email)
    if UserRole.objects.filter(org_id=org.org_id, user__email__iexact=normalized_email).exists():
        raise ValueError("User is already a member of this organization.")

    token = generate_invite_token()

    try:
        invite = OrganizationInviteRepository.create(
            org=org,
            email=normalized_email,
            role=role,
            token=token,
            invited_by=invited_by,
        )
    except IntegrityError as exc:
        raise ValueError("This email has already been invited to the organization.") from exc

    transaction.on_commit(
        lambda: send_invite_email(email=normalized_email, org_name=org.name, token=token)
    )
    return invite


def accept_invite(*, token: str, password: str) -> OrganizationInvite:
    invite = OrganizationInviteRepository.get_by_token(token)
    if invite is None:
        raise ValueError("Invite token is invalid.")
    if invite.status != InviteStatus.INVITED:
        raise ValueError("Invite has already been accepted.")

    normalized_email = _normalize_email(invite.email)
    UserModel = get_user_model()

    with transaction.atomic():
        user = UserModel.objects.filter(email__iexact=normalized_email).first()
        if user is None:
            username = _generate_unique_username(
                UserModel, _base_username_from_email(normalized_email)
            )
            user = UserModel.objects.create_user(
                username=username,
                email=normalized_email,
                password=password,
            )
        else:
            user.set_password(password)
            user.save()

        UserRole.objects.update_or_create(
            user=user,
            org=invite.org,
            defaults={"role": invite.role},
        )

        invite.status = InviteStatus.ACTIVE
        invite.accepted_at = timezone.now()
        invite.accepted_user = user
        invite.save(update_fields=["status", "accepted_at", "accepted_user"])

    return invite
