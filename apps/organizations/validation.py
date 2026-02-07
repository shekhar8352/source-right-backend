from __future__ import annotations

from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from rest_framework import serializers


def _normalize_allowed(values: object) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        items = values.split(",")
    else:
        try:
            items = list(values)  # type: ignore[arg-type]
        except TypeError:
            items = [str(values)]
    normalized = [str(item).strip().upper() for item in items if str(item).strip()]
    return normalized


def get_allowed_countries() -> list[str]:
    return _normalize_allowed(getattr(settings, "ALLOWED_COUNTRIES", []))


def get_allowed_currencies() -> list[str]:
    return _normalize_allowed(getattr(settings, "ALLOWED_CURRENCIES", []))


def get_default_base_currency() -> str:
    value = getattr(settings, "DEFAULT_BASE_CURRENCY", "")
    if value is None:
        return ""
    return str(value).strip().upper()


def get_default_org_timezone() -> str:
    value = getattr(settings, "DEFAULT_ORG_TIMEZONE", "UTC")
    if value is None:
        return "UTC"
    return str(value).strip() or "UTC"


def normalize_code(value: str) -> str:
    return value.strip().upper()


def normalize_timezone(value: str) -> str:
    return value.strip()


def validate_in_allowed(value: str, allowed: Iterable[str], field_name: str) -> None:
    if allowed and value not in allowed:
        raise serializers.ValidationError(
            f"{field_name} must be one of: {', '.join(sorted(allowed))}."
        )


def validate_timezone_identifier(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise serializers.ValidationError("Invalid timezone.") from exc
