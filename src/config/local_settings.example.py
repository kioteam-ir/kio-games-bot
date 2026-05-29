import os

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-me",
)
DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

_allowed = os.environ.get("ALLOWED_HOST", "localhost 127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in _allowed.replace(",", " ").split() if host.strip()]

LOCAL_DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "4fall_bot"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
