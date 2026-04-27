from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# USE_LOCAL_SQLITE=1 força SQLite. Com 0, usa DATABASE_URL (ex.: Neon) — não precisa de Railway
_use_sqlite = os.environ.get("USE_LOCAL_SQLITE", "").lower() in ("1", "true", "yes")
if _use_sqlite or not (DATABASE_URL or "").strip():
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Console email backend for local dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Sem Redis: Celery em modo “eager” (não exige serviço no Railway)
_celery_eager = os.environ.get("CELERY_EAGER", "true").lower() in ("1", "true", "yes", "")
CELERY_TASK_ALWAYS_EAGER = _celery_eager
if CELERY_TASK_ALWAYS_EAGER:
    CELERY_BROKER_URL = "memory://"

try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass
