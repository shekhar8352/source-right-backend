from __future__ import annotations

from rest_framework import serializers

from .models import Organization
from .validation import (
    get_allowed_countries,
    get_allowed_currencies,
    get_default_base_currency,
    normalize_code,
    validate_in_allowed,
)


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    country = serializers.CharField(allow_blank=False, trim_whitespace=True)
    base_currency = serializers.CharField(allow_blank=False, trim_whitespace=True, required=False)
    created_by_id = serializers.IntegerField(required=False, write_only=True)

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
        return attrs


class OrganizationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "org_id",
            "name",
            "country",
            "base_currency",
            "status",
            "created_at",
        )
        read_only_fields = fields


class OrganizationInviteAcceptResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    org_id = serializers.CharField()
