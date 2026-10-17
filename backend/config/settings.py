import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = os.environ.get
def flag(key, default=False):
    return str(env(key, default)).lower() in ("1", "true", "yes")

DEBUG = flag("DJANGO_DEBUG")
SECRET_KEY = env("DJANGO_SECRET_KEY") or ("dev-only-insecure-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off.")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "core",
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
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages"]},
}]

# ---- Persistent storage: keep OUTSIDE the replaceable source directory in production ----
DATA_ROOT = Path(env("AUTOMCS_DATA_ROOT", BASE_DIR.parent / "data"))
MODELS_ROOT = Path(env("AUTOMCS_MODELS_ROOT", BASE_DIR.parent / "models"))
ORIGINALS_DIR = DATA_ROOT / "originals"
EXPORTS_DIR = DATA_ROOT / "exports"
TEMP_DIR = DATA_ROOT / "temporary"
for _d in (ORIGINALS_DIR, EXPORTS_DIR, TEMP_DIR, MODELS_ROOT):
    _d.mkdir(parents=True, exist_ok=True)

if env("POSTGRES_HOST"):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql", "NAME": env("POSTGRES_DB", "automcs"),
        "USER": env("POSTGRES_USER", "automcs"), "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST"), "PORT": env("POSTGRES_PORT", "5432")}}
else:  # dev / tests only
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [{"NAME": f"django.contrib.auth.password_validation.{n}"} for n in (
    "UserAttributeSimilarityValidator", "MinimumLengthValidator",
    "CommonPasswordValidator", "NumericPasswordValidator")]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "UTC"; USE_TZ = True
STATIC_URL = "static/"; STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "1200/min", "login": "10/min", "contact": "5/hour"},
}

SECURE = flag("DJANGO_SECURE", not DEBUG)
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE
SECURE_SSL_REDIRECT = SECURE and flag("DJANGO_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = 31536000 if SECURE else 0
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SAMESITE = "Lax"
DATA_UPLOAD_MAX_NUMBER_FILES = 1000
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

CELERY_BROKER_URL = env("REDIS_URL", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = flag("CELERY_EAGER")   # dev only: run tasks inline
CELERY_TASK_ACKS_LATE = True

AUTOMCS = {
    "MAX_UPLOAD_BYTES": int(env("MAX_UPLOAD_MB", 50)) * 1024 * 1024,
    "MAX_BATCH_FILES": int(env("MAX_BATCH_FILES", 200)),
    "ROUNDING": "ROUND_HALF_UP",        # confirm against the research protocol
    "GEMINI_API_KEY": env("GEMINI_API_KEY", ""),
    "GEMINI_MODEL": env("GEMINI_MODEL", ""),   # also editable by an admin in SiteSettings
    "LOCAL_MODEL_REPO": env("LOCAL_MODEL_REPO", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"),
    "LOCAL_MODEL_REVISION": env("LOCAL_MODEL_REVISION", ""),  # MUST be a pinned commit hash
    "LOCAL_MODEL_DIR": Path(env("LOCAL_MODEL_DIR", MODELS_ROOT / "deepseek-1.5b")),
    "AUTO_DOWNLOAD": flag("LOCAL_MODEL_AUTO_DOWNLOAD", True),
    "OCR_ENGINE": env("OCR_ENGINE", "tesseract"),
}
LOGGING = {"version": 1, "disable_existing_loggers": False,
           "handlers": {"c": {"class": "logging.StreamHandler"}}, "root": {"handlers": ["c"], "level": "INFO"}}
