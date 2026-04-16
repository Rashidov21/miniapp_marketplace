"""
Django settings for miniapp_marketplace.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.users",
    "apps.shops",
    "apps.products",
    "apps.orders",
    "apps.platform",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.platform.middleware.AnalyticsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.core.context_processors.static_asset_version",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "miniapp_marketplace"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

if os.environ.get("USE_SQLITE", "").lower() in ("1", "true", "yes"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "uz"

LANGUAGES = [
    ("uz", "Oʻzbekcha"),
    ("ru", "Русский"),
]

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Query string for /static/js/app.js etc. when not using ManifestStaticFilesStorage (e.g. misconfigured nginx).
STATIC_ASSET_VERSION = os.environ.get("STATIC_ASSET_VERSION", "20260417")

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Production: ManifestStaticFilesStorage → hashed filenames (e.g. app.abc12.js) for cache busting.
# Dev: StaticFilesStorage → plain names; runserver works without collectstatic.
# Django 5+ requires both "default" (uploads) and "staticfiles" keys in STORAGES.
if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_ROOT},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_ROOT},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
# Related pitfalls (not fixed by this alone):
# - Nginx must serve the whole STATIC_ROOT tree (hashed files + manifest).
# - External scripts (telegram.org, cdn.tailwindcss.com) use their own cache; pin or self-host if needed.
# - Deploy: collectstatic --noinput then reload Gunicorn; long Cache-Control on /static/ is OK with hashes.

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Freshness window for Telegram WebApp initData (auth_date), seconds. Default 24h.
TELEGRAM_INITDATA_MAX_AGE_SECONDS = int(os.environ.get("TELEGRAM_INITDATA_MAX_AGE_SECONDS", "86400"))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "miniapp-marketplace",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.TelegramInitDataAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "order_create": os.environ.get("API_ORDER_CREATE_THROTTLE", "60/hour"),
    },
}

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

_session_cookie_secure_raw = os.environ.get("SESSION_COOKIE_SECURE", "").strip().lower()
if _session_cookie_secure_raw in ("1", "true", "yes"):
    SESSION_COOKIE_SECURE = True
elif _session_cookie_secure_raw in ("0", "false", "no"):
    SESSION_COOKIE_SECURE = False
else:
    # Bo‘sh: prod da HTTPS cookie, dev da oddiy.
    SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")

# Landing arizalari — Telegram chat ID lar (vergul bilan), masalan: "123456789" yoki "111,222"
LANDING_NOTIFY_TELEGRAM_IDS = os.environ.get("LANDING_NOTIFY_TELEGRAM_IDS", "")

# Telegram: bir chat uchun kuniga maks. necha marta kechikkan onboarding xabarlari ketma-ketligi
BOT_ONBOARDING_MAX_PER_DAY = int(os.environ.get("BOT_ONBOARDING_MAX_PER_DAY", "6"))

# Sotuvchi oferta / foydalanish shartlari versiyasi; yangilanganda foydalanuvchi qayta tasdiqlashi kerak.
CURRENT_SELLER_TERMS_VERSION = os.environ.get("CURRENT_SELLER_TERMS_VERSION", "1").strip() or "1"

# Mijoz to‘lovi (Click): keyingi integratsiya uchun muhit o‘zgaruvchilari shu yerda ulanadi
# (masalan CLICK_MERCHANT_ID va h.k.) — hozircha kodda ishlatilmaydi; obuna monetizatsiyasi o‘zgarmaydi.

# Monetizatsiya: FREE tier (trial ham shu limitda), trafik upsell bosqichi
MONETIZATION_FREE_MAX_PRODUCTS = int(os.environ.get("MONETIZATION_FREE_MAX_PRODUCTS", "5"))
MONETIZATION_UPSELL_MIN_VIEWS_WEEK = int(os.environ.get("MONETIZATION_UPSELL_MIN_VIEWS_WEEK", "80"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGIN_URL = "/platform/login/"
LOGIN_REDIRECT_URL = "/platform/"
LOGOUT_REDIRECT_URL = "/platform/login/"

# --- Logging (prod: DJANGO_LOG_LEVEL=INFO) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "DEBUG" if DEBUG else "INFO"),
    },
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps.orders": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.shops": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.platform": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.core.telegram": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# --- DEBUG=False uchun xavfsizlik (Nginx HTTPS + proxy) ---
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "true"
    ).lower() in ("1", "true", "yes")
    SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "true").lower() in (
        "1",
        "true",
        "yes",
    )
