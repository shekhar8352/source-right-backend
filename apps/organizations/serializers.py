from __future__ import annotations

from rest_framework import serializers

from .models import Organization
from .validation import (
    get_allowed_countries,
    get_allowed_currencies,
    get_default_base_currency,
    get_default_org_timezone,
    normalize_code,
    normalize_timezone,
    validate_timezone_identifier,
    validate_in_allowed,
)


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    country = serializers.CharField(allow_blank=False, trim_whitespace=True)
    base_currency = serializers.CharField(allow_blank=False, trim_whitespace=True, required=False)
    timezone = serializers.CharField(allow_blank=False, trim_whitespace=True, required=False)
    created_by_id = serializers.IntegerField(required=False, write_only=True)
    creator_username = serializers.CharField(
        required=False, allow_blank=False, trim_whitespace=True
    )
    creator_email = serializers.EmailField(required=False, allow_blank=False)
    creator_password = serializers.CharField(required=False, allow_blank=False, write_only=True)
    creator_first_name = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True
    )
    creator_last_name = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True
    )

    def validate_name(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Organization name cannot be empty.")
        return normalized

    def validate_country(self, value: str) -> str:
        normalized = normalize_code(value)
        allowed = get_allowed_countries()
        validate_in_allowed(normalized, allowed, "Country")
        return normalized

    def validate_base_currency(self, value: str) -> str:
        normalized = normalize_code(value)
        allowed = get_allowed_currencies()
        validate_in_allowed(normalized, allowed, "Base currency")
        return normalized

    def validate_timezone(self, value: str) -> str:
        normalized = normalize_timezone(value)
        validate_timezone_identifier(normalized)
        return normalized

    def validate(self, attrs):
        if "base_currency" not in attrs:
            default_currency = get_default_base_currency()
            if not default_currency:
                raise serializers.ValidationError(
                    {"base_currency": "Base currency is required."}
                )
            allowed = get_allowed_currencies()
            validate_in_allowed(default_currency, allowed, "Base currency")
            attrs["base_currency"] = default_currency
        if "timezone" not in attrs:
            timezone = get_default_org_timezone()
            validate_timezone_identifier(timezone)
            attrs["timezone"] = timezone
        return attrs


class OrganizationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "org_id",
            "name",
            "country",
            "base_currency",
            "timezone",
            "status",
            "created_at",
        )
        read_only_fields = fields


class OrganizationSettingsSerializer(serializers.Serializer):
    org_id = serializers.CharField(read_only=True)
    base_currency = serializers.CharField()
    country = serializers.CharField()
    timezone = serializers.CharField()


class OrganizationSettingsUpdateSerializer(serializers.Serializer):
    base_currency = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    country = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    timezone = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)

    def validate_base_currency(self, value: str) -> str:
        normalized = normalize_code(value)
        allowed = get_allowed_currencies()
        validate_in_allowed(normalized, allowed, "Base currency")
        return normalized

    def validate_country(self, value: str) -> str:
        normalized = normalize_code(value)
        allowed = get_allowed_countries()
        validate_in_allowed(normalized, allowed, "Country")
        return normalized

    def validate_timezone(self, value: str) -> str:
        normalized = normalize_timezone(value)
        validate_timezone_identifier(normalized)
        return normalized

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                {"detail": "At least one setting must be provided."}
            )
        return attrs


class OrganizationInviteAcceptResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    org_id = serializers.CharField()


class OrganizationUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    is_active = serializers.BooleanField()
    role = serializers.CharField()
