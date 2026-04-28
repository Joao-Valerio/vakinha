import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# BASE_DIR = pasta vakinha_django
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BASE_DIR / ".env")
load_dotenv(_BASE_DIR.parent / ".env", override=True)
BASE_DIR = _BASE_DIR

from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY must be set as an environment variable for security. "
        "Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "crispy_forms",
    "crispy_tailwind",
    "django_celery_results",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.campaigns",
    "apps.payments",
    "apps.dashboard",
    "apps.notifications",
    "apps.ai_agent",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================
# PAGAMENTOS (MercadoPago)
# ============================================
MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_WEBHOOK_SECRET = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "")

if not MERCADOPAGO_ACCESS_TOKEN and not DEBUG:
    import warnings
    warnings.warn("MERCADOPAGO_ACCESS_TOKEN not configured - payments will fail", stacklevel=2)

# ============================================
# SITE & URLS
# ============================================
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

# ============================================
# ARTIFICIAL INTELLIGENCE & LLMs
# ============================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "6"))
GEMINI_RETRY_BASE_SECONDS = float(os.environ.get("GEMINI_RETRY_BASE_SECONDS", "2.0"))
GEMINI_NUM_HISTORY_RUNS = int(os.environ.get("GEMINI_NUM_HISTORY_RUNS", "2"))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ============================================
# EVOLUTION API (WhatsApp)
# ============================================
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "")
EVOLUTION_TOKEN = os.environ.get("EVOLUTION_TOKEN", "")

if not all([EVOLUTION_API_URL, EVOLUTION_INSTANCE, EVOLUTION_TOKEN]) and not DEBUG:
    import warnings
    warnings.warn("Evolution API not fully configured - WhatsApp features will be limited", stacklevel=2)

# ============================================
# WEBHOOKS & SECURITY
# ============================================
AI_WEBHOOK_TOKEN = os.environ.get("AI_WEBHOOK_TOKEN", "")

# ============================================
# DONATIONS
# ============================================
DONATION_PRESET_AMOUNTS = [10, 25, 50, 100, 250, 500]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database — configured per environment, default Neon via DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or "sqlite:///db.sqlite3",
        conn_max_age=0,
        ssl_require=bool(
            (DATABASE_URL or "").startswith("postgres")
        ),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Vakinha IA <noreply@vakinha.ai>")

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_PUBLIC_KEY = os.environ.get("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_WEBHOOK_SECRET = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "")

# Evolution API (WhatsApp)
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "")
EVOLUTION_TOKEN = os.environ.get("EVOLUTION_TOKEN", "")

# AI Agent
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Limite/retries: ver .env.example (429 Too Many Requests no plano free)
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "6"))
GEMINI_RETRY_BASE_SECONDS = float(os.environ.get("GEMINI_RETRY_BASE_SECONDS", "2.0"))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
AI_WEBHOOK_TOKEN = os.environ.get("AI_WEBHOOK_TOKEN", "change-me-secret-token")

# Site URL
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

# Logging
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
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
