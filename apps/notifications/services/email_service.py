from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.core.mail import send_mail


def send_email(*, subject: str, message: str, recipients: Iterable[str], from_email: str | None = None) -> int:
    resolved_from = from_email or getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@sourceright.local"
    )
    return send_mail(subject, message, resolved_from, list(recipients))
