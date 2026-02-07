from rest_framework import serializers

from apps.organizations.validation import (
    get_allowed_countries,
    normalize_code,
    normalize_timezone,
    validate_in_allowed,
    validate_timezone_identifier,
)


class VendorCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    country = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    timezone = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)

    def validate_country(self, value: str) -> str:
        normalized = normalize_code(value)
        validate_in_allowed(normalized, get_allowed_countries(), "Country")
        return normalized

    def validate_timezone(self, value: str) -> str:
        normalized = normalize_timezone(value)
        validate_timezone_identifier(normalized)
        return normalized


class VendorResponseSerializer(serializers.Serializer):
    vendor_id = serializers.CharField()
    org_id = serializers.CharField()
    name = serializers.CharField()
    country = serializers.CharField()
    timezone = serializers.CharField()
