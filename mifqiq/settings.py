"""
Django settings for mifqiq project.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

SECRET_KEY = config("MY_SECRET_KEY")
DEBUG = os.getenv("MY_DEBUG", "False").strip().lower() in {"1", "true", "yes", "on"}
if not DEBUG and (
    len(SECRET_KEY) < 50
    or len(set(SECRET_KEY)) < 5
    or SECRET_KEY.startswith("django-insecure-")
):
    raise ImproperlyConfigured(
        "MY_SECRET_KEY must be a strong, randomly generated key in production."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1, mifqiq-production.up.railway.app",
    ).split(",")
    if host.strip()
]

# SECURITY
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
else:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Strict"

SITE_ID = 2

X_FRAME_OPTIONS = "DENY"
# APPLICATIONS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "professors_fqiq",
    "pwa",
    "drf_spectacular",
    "rest_framework",
    "rest_framework.authtoken",
]

# MIDDLEWARE
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# AUTHENTICATION
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# ALLAUTH
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_ADAPTER = "professors_fqiq.core.adapters.NoLocalSignupAccountAdapter"

SOCIALACCOUNT_ADAPTER = "professors_fqiq.core.adapters.UNMSMSocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"prompt": "select_account", "hd": "unmsm.edu.pe"},
    }
}

# REDIRECTS
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/completar-perfil/"
LOGOUT_REDIRECT_URL = "/"

CSRF_TRUSTED_ORIGINS = [
    "https://mifqiq-production.up.railway.app",
]

# URLS AND TEMPLATES
ROOT_URLCONF = "mifqiq.urls"
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
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "mifqiq.wsgi.application"

# DATABASE
database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "CONN_HEALTH_CHECKS": True,
        }
    }
elif database_url:
    DATABASES = {
        "default": dj_database_url.parse(database_url, conn_max_age=600)
    }
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
else:
    raise ImproperlyConfigured(
        "DATABASE_URL (or DATABASE_PUBLIC_URL) must be configured for the production database."
    )

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# STATIC AND MEDIA FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

if DEBUG:
    STATICFILES_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_BACKEND = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": STATICFILES_BACKEND,
    },
}

WHITENOISE_USE_FINDERS = DEBUG

# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "professors_fqiq": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django.request": {"handlers": ["console"], "level": "WARNING"},
        "django.security": {"handlers": ["console"], "level": "WARNING"},
    },
}

# FILE UPLOADS
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST FRAMEWORK AND JWT
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=15),
}

# EMAIL
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default=EMAIL_HOST_USER or "webmaster@localhost",
)

if not DEBUG and not (EMAIL_HOST_USER and EMAIL_HOST_PASSWORD):
    raise ImproperlyConfigured(
        "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be configured in production."
    )

# PWA
PWA_APP_NAME = "Mi FQIQ"
PWA_APP_THEME_COLOR = "#F5F5F8"
PWA_APP_BACKGROUND = "#F5F5F8"
PWA_APP_ICONS = [
    {
        "src": "/static/images/icons/icon-192x192.png",
        "sizes": "192x192",
        "type": "image/png",
    },
]
