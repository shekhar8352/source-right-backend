from __future__ import annotations

from rest_framework import serializers


class MeUserSerializer(serializers.Serializer):
    """Minimal user payload for /me (Redux / dashboard)."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    primary_role = serializers.CharField()
    date_joined = serializers.DateTimeField()


class MeOrganizationSerializer(serializers.Serializer):
    """Minimal organization payload for /me (Redux / dashboard)."""

    org_id = serializers.CharField()
    name = serializers.CharField()
    country = serializers.CharField()
    base_currency = serializers.CharField()
    timezone = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    """Response for GET /me: current user and organization (null if setup token)."""

    user = MeUserSerializer()
    organization = MeOrganizationSerializer(allow_null=True)
    role = serializers.CharField(allow_null=True)
