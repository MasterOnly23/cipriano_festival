from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return (value or "").strip().strip('"').strip("'")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,*").split(",")]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,https://*.trycloudflare.com",
    ).split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "festival",
]

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

ROOT_URLCONF = "cipriano.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cipriano.wsgi.application"
ASGI_APPLICATION = "cipriano.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = os.getenv("USE_X_FORWARDED_HOST", "1") == "1"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "0") == "1"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

ADMIN_ACTIONS_PIN = env_value("ADMIN_ACTIONS_PIN", "1234")
ADMIN_OVERRIDE_PIN = env_value("ADMIN_OVERRIDE_PIN", ADMIN_ACTIONS_PIN)
AUTH_SESSION_MINUTES = int(os.getenv("AUTH_SESSION_MINUTES", "480"))

DEFAULT_FESTIVAL_KITCHEN_PIN = env_value("DEFAULT_FESTIVAL_KITCHEN_PIN", env_value("DEFAULT_KITCHEN_PIN", "1111"))
DEFAULT_FESTIVAL_SALES_PIN = env_value("DEFAULT_FESTIVAL_SALES_PIN", env_value("DEFAULT_SALES_PIN", "2222"))
DEFAULT_FESTIVAL_SECONDARY_SALES_PIN = env_value("DEFAULT_FESTIVAL_SECONDARY_SALES_PIN", "2323")
DEFAULT_FESTIVAL_BATCHES_PIN = env_value("DEFAULT_FESTIVAL_BATCHES_PIN", env_value("DEFAULT_BATCHES_PIN", "3333"))
DEFAULT_CIPRIANO_CAJALOCAL_PIN = env_value("DEFAULT_CIPRIANO_CAJALOCAL_PIN", "2211")
DEFAULT_CIPRIANO_CAJAOPERACION_PIN = env_value("DEFAULT_CIPRIANO_CAJAOPERACION_PIN", "2212")
DEFAULT_CIPRIANO_ADMINISTRADOR_PIN = env_value("DEFAULT_CIPRIANO_ADMINISTRADOR_PIN", "2299")
DEFAULT_CIPRIANO_OPERADOR_PIN = env_value("DEFAULT_CIPRIANO_OPERADOR_PIN", "2288")
DEFAULT_CIPRIANO_SOCIO_PIN = env_value("DEFAULT_CIPRIANO_SOCIO_PIN", "2277")
DEFAULT_BURGERS_KITCHEN_PIN = env_value("DEFAULT_BURGERS_KITCHEN_PIN", "4444")
DEFAULT_BURGERS_SALES_PIN = env_value("DEFAULT_BURGERS_SALES_PIN", "5555")
DEFAULT_BURGERS_SECONDARY_SALES_PIN = env_value("DEFAULT_BURGERS_SECONDARY_SALES_PIN", "5656")
DEFAULT_BURGERS_BATCHES_PIN = env_value("DEFAULT_BURGERS_BATCHES_PIN", "6666")
DEFAULT_DON_CAJALOCAL_PIN = env_value("DEFAULT_DON_CAJALOCAL_PIN", "5511")
DEFAULT_DON_CAJAOPERACION_PIN = env_value("DEFAULT_DON_CAJAOPERACION_PIN", "5512")
DEFAULT_DON_ADMINISTRADOR_PIN = env_value("DEFAULT_DON_ADMINISTRADOR_PIN", "5599")
DEFAULT_DON_OPERADOR_PIN = env_value("DEFAULT_DON_OPERADOR_PIN", "5588")
DEFAULT_DON_SOCIO_PIN = env_value("DEFAULT_DON_SOCIO_PIN", "5577")
DEFAULT_ADMIN_LOGIN_PIN = env_value("DEFAULT_ADMIN_LOGIN_PIN", "9999")
