from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .domain.enums import RoleType
from .models import OrganizationInvite


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
