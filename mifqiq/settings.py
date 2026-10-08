"""
Django settings for mifqiq project.
"""

import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

SECRET_KEY = config('MY_SECRET_KEY')
DEBUG = os.getenv("MY_DEBUG") == "True"


ALLOWED_HOSTS = ["localhost", "mifqiq-production.up.railway.app"]

#SECURITY (HTTPS / COOKIES / HSTS)
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

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'


# HEADERS DE SEGURIDAD
SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'", "fonts.googleapis.com", "*.google.com"),
    'style-src': ("'self'", "'unsafe-inline'", "fonts.googleapis.com"),
    'img-src': ("'self'", "data:", "https:"),
    'font-src': ("'self'", "fonts.gstatic.com"),
}

X_FRAME_OPTIONS = 'DENY'


# APPLICATIONS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # app
    'professors_fqiq',
    #PWA
    'pwa',

    #API
    'drf_spectacular',
    'rest_framework',
    'rest_framework.authtoken',
    
]



SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# ALLAUTH

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {},
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True

SOCIALACCOUNT_ADAPTER = 'professors_fqiq.adapters.RestrictDomainSocialAccountAdapter'

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_LOGIN_CANCELLED_URL = "account_3rdparty_login_cancelled"

LOGIN_REDIRECT_URL = '/professors/'
LOGIN_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# TEMPLATES


ROOT_URLCONF = 'mifqiq.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = 'mifqiq.wsgi.application'


# DATABASE


DATABASES = {
    "default": dj_database_url.config(default=os.getenv("DATABASE_URL"))
    }

# PASSWORD VALIDATION

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNATIONALIZATION


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Lima'

USE_I18N = True
USE_TZ = True


# STATIC FILES

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE="whitenoise.storage.CompressedManifestStaticFilesStorage"

# backend dinámico (clave)
if DEBUG:
    STATICFILES_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_BACKEND = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# STORAGES (DJANGO 5+)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": STATICFILES_BACKEND,
    },
}

# mejora en dev
WHITENOISE_USE_FINDERS = DEBUG


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# LOGGING

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'professors_fqiq': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}


# UPLOAD LIMITS

FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644


# DEFAULT PK

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#API
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        ]
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
}


# EMAIL CONFIGURATION

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'ramirezsantiago2503@gmail.com'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


#PWA
PWA_APP_NAME = "Mi FQIQ"
PWA_APP_THEME_COLOR= '#F5F5F8'
PWA_APP_BACKGROUND = '#F5F5F8'

PWA_APP_ICONS = [
    {
        "src": "/static/images/icons/icon-192x192.png",
        "sizes": "192x192",
        "type": "image/png"
    },
    
]
