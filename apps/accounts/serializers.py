from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.access_control.domain.enums import RoleType

User = get_user_model()


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True, allow_blank=False)
    role = serializers.ChoiceField(choices=RoleType.choices)
    org_id = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    first_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    last_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate_username(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Username cannot be empty.")
        if User.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return normalized

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return normalized

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        org_id = attrs.get("org_id")
        if role != RoleType.ORG_ADMIN and not org_id:
            raise serializers.ValidationError(
                {"org_id": "org_id is required for non-ORG_ADMIN roles."}
            )
        return attrs


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    primary_role = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_joined = serializers.DateTimeField()


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, allow_blank=False)

    def validate(self, attrs):
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError(
                {"detail": "username or email is required."}
            )
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
