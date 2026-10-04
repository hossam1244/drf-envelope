SECRET_KEY = "test-only-insecure-key"
DEBUG = False
ALLOWED_HOSTS = ["*"]
USE_TZ = True
ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_envelope",
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.BasicAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "EXCEPTION_HANDLER": "drf_envelope.handler.envelope_exception_handler",
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
