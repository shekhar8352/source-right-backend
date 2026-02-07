from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager as DjangoUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone

from apps.access_control.domain.enums import RoleType


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class UserQuerySet(models.QuerySet):
    def delete(self):  # pragma: no cover - used for safety
        return self.update(status=UserStatus.INACTIVE, is_active=False)


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    pass

class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        validators=[username_validator],
        error_messages={"unique": "A user with that username already exists."},
    )
    first_name = models.CharField("first name", max_length=150, blank=True)
    last_name = models.CharField("last name", max_length=150, blank=True)
    email = models.EmailField("email address", unique=True)
    primary_role = models.CharField(
        max_length=40,
        choices=RoleType.choices,
    )
    password = models.CharField("password", max_length=128)
    last_login = models.DateTimeField("last login", blank=True, null=True)
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text="Designates whether this user should be treated as active.",
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)
    is_superuser = models.BooleanField(
        "superuser status",
        default=False,
        help_text="Designates that this user has all permissions without explicitly assigning them.",
    )
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_name="user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="user_set",
        related_query_name="user",
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "primary_role"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.username

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name

    def get_short_name(self) -> str:
        return self.first_name or self.username

    def soft_delete(self) -> None:
        if self.status != UserStatus.INACTIVE or self.is_active:
            self.status = UserStatus.INACTIVE
            self.is_active = False
            self.save(update_fields=["status", "is_active"])

    def delete(self, using=None, keep_parents=False):  # pragma: no cover - safety
        self.soft_delete()
        return (1, {self._meta.label: 1})
