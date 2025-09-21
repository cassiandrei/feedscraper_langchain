from .base import *
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = [
    get_env_variable("ALLOWED_HOST", "localhost"),
]

# Database for production (PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env_variable("DATABASE_NAME"),
        "USER": get_env_variable("DATABASE_USER"),
        "PASSWORD": get_env_variable("DATABASE_PASSWORD"),
        "HOST": get_env_variable("DATABASE_HOST"),
        "PORT": get_env_variable("DATABASE_PORT"),
    }
}

# Alternative: Use DATABASE_URL for cloud deployments
if get_env_variable("DATABASE_URL", None):
    DATABASES["default"] = dj_database_url.parse(get_env_variable("DATABASE_URL"))

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# APScheduler for production (PostgreSQL)
SCHEDULER_CONFIG.update(
    {
        "apscheduler.jobstores.default": {
            "type": "sqlalchemy",
            "url": f'postgresql://{get_env_variable("DATABASE_USER")}:'
            f'{get_env_variable("DATABASE_PASSWORD")}@'
            f'{get_env_variable("DATABASE_HOST")}:'
            f'{get_env_variable("DATABASE_PORT")}/'
            f'{get_env_variable("DATABASE_NAME")}',
        },
    }
)

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 86400
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS for production
CORS_ALLOWED_ORIGINS = [
    get_env_variable("FRONTEND_URL", "http://localhost:3000"),
]

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_variable("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(get_env_variable("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD", "")

# Production logging
LOGGING["handlers"]["file"]["filename"] = "/var/log/feedscraper/app.log"
