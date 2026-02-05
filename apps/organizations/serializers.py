from __future__ import annotations

from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password

from .domain.enums import RoleType
from .models import Organization, OrganizationInvite
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


class OrganizationInviteCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=RoleType.choices)

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise serializers.ValidationError("Email is required.")
        return normalized


class OrganizationInviteResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvite
        fields = (
            "id",
            "email",
            "role",
            "status",
            "invited_at",
        )
        read_only_fields = fields


class OrganizationInviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(allow_blank=False, trim_whitespace=True)
    password = serializers.CharField(allow_blank=False, trim_whitespace=True, write_only=True)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value
