from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True, allow_blank=False)
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


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_joined = serializers.DateTimeField()
