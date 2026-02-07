from rest_framework import serializers

from apps.organizations.validation import (
    get_allowed_countries,
    get_allowed_currencies,
    normalize_code,
    normalize_timezone,
    validate_in_allowed,
    validate_timezone_identifier,
)


class InvoiceSummarySerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    amount = serializers.IntegerField()
    status = serializers.CharField()


class InvoiceListResponseSerializer(serializers.Serializer):
    invoices = InvoiceSummarySerializer(many=True)


class InvoiceApproveResponseSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    status = serializers.CharField()


class InvoiceUploadSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    amount = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    country = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    timezone = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)

    def validate_currency(self, value: str) -> str:
        normalized = normalize_code(value)
        validate_in_allowed(normalized, get_allowed_currencies(), "Base currency")
        return normalized

    def validate_country(self, value: str) -> str:
        normalized = normalize_code(value)
        validate_in_allowed(normalized, get_allowed_countries(), "Country")
        return normalized

    def validate_timezone(self, value: str) -> str:
        normalized = normalize_timezone(value)
        validate_timezone_identifier(normalized)
        return normalized


class InvoiceUploadResponseSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    status = serializers.CharField()
    currency = serializers.CharField()
    country = serializers.CharField()
    timezone = serializers.CharField()
