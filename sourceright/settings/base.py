import os
from pathlib import Path

from dotenv import load_dotenv

from shared.logging.config import build_logging_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def require_env(name: str, allow_empty: bool = False) -> str:
    if name not in os.environ:
        raise RuntimeError(f"Missing required environment variable: {name}")
    value = os.environ.get(name, "")
    if not allow_empty and value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def parse_csv_env(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


SECRET_KEY = require_env("DJANGO_SECRET_KEY")
DEBUG = parse_bool(require_env("DJANGO_DEBUG"))
ALLOWED_HOSTS = [
    host.strip() for host in require_env("DJANGO_ALLOWED_HOSTS").split(",") if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "rest_framework",
    "django_celery_results",
    "django_celery_beat",
    "apps.accounts",
    "apps.notifications",
    "apps.access_control",
    "apps.core",
    "apps.organizations",
    "apps.healthcheck",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "shared.logging.middleware.LoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.organizations.middleware.OrganizationContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sourceright.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "sourceright.wsgi.application"
ASGI_APPLICATION = "sourceright.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": require_env("POSTGRES_DB"),
        "USER": require_env("POSTGRES_USER"),
        "PASSWORD": require_env("POSTGRES_PASSWORD"),
        "HOST": require_env("POSTGRES_HOST"),
        "PORT": require_env("POSTGRES_PORT"),
    }
}

REDIS_HOST = require_env("REDIS_HOST")
REDIS_PORT = require_env("REDIS_PORT")
REDIS_DB = require_env("REDIS_DB")
REDIS_PASSWORD = require_env("REDIS_PASSWORD", allow_empty=True)

if REDIS_PASSWORD:
    REDIS_AUTH = f":{REDIS_PASSWORD}@"
else:
    REDIS_AUTH = ""

REDIS_URL = f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = require_env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = require_env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

LOGGING = build_logging_config(base_dir=BASE_DIR)

ALLOWED_COUNTRIES = parse_csv_env("ALLOWED_COUNTRIES")
ALLOWED_CURRENCIES = parse_csv_env("ALLOWED_CURRENCIES")
DEFAULT_BASE_CURRENCY = os.environ.get("DEFAULT_BASE_CURRENCY", "").strip().upper()

ORG_CONTEXT_HEADER = os.environ.get("ORG_CONTEXT_HEADER", "X-Org-Id")
ORG_CONTEXT_ENFORCED_PREFIXES = ["/api/"]
ORG_CONTEXT_EXEMPT_PATHS = [
    "/api/organizations",
    "/api/organizations/invites/accept",
    "/api/health/live",
    "/api/health/ready",
]

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@sourceright.local")
INVITE_ACCEPT_URL_BASE = os.environ.get("INVITE_ACCEPT_URL_BASE", "").strip()
