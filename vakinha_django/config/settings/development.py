from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use SQLite locally if DATABASE_URL not set
if not DATABASE_URL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Console email backend for local dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery eager mode for local dev (tasks run synchronously)
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_EAGER", "false").lower() == "true"

try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass
