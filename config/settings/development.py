from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Database for development (SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Development specific settings
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development logging
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"]["django"]["level"] = "DEBUG"

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# APScheduler for development (SQLite)
SCHEDULER_CONFIG["apscheduler.jobstores.default"] = {
    "type": "sqlalchemy",
    "url": f"sqlite:///{BASE_DIR}/scheduler_dev.db",
}
