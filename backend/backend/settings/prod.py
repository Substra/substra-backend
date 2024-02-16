import os

from substrapp.storages.minio import MinioStorage

from .common import *
from .deps.ledger import *
from .deps.org import *
from .deps.restframework import *
from .mods.cors import *
from .mods.oidc import *

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
os.environ["HTTPS"] = "on"
os.environ["wsgi.url_scheme"] = "https"

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 365 * 24 * 3600))  # 1 year
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATIC_ROOT = BASE_DIR / "statics"

DATASAMPLE_BUCKET_NAME = "substra-datasample"
DATASAMPLE_STORAGE = MinioStorage(DATASAMPLE_BUCKET_NAME)

MODEL_BUCKET_NAME = "substra-model"
MODEL_STORAGE = MinioStorage(MODEL_BUCKET_NAME)

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", f"/substra/medias/{ORG_NAME}")
SERVERMEDIAS_ROOT = os.environ.get("SERVERMEDIAS_ROOT", f"/substra/servermedias/{ORG_NAME}")
FUNCTION_BUCKET_NAME = "substra-function"
FUNCTION_STORAGE = MinioStorage(FUNCTION_BUCKET_NAME)

DATAMANAGER_BUCKET_NAME = "substra-datamanager"
DATAMANAGER_STORAGE = MinioStorage(DATAMANAGER_BUCKET_NAME)

ASSET_LOGS_BUCKET_NAME = "substra-asset-logs"
ASSET_LOGS_STORAGE = MinioStorage(ASSET_LOGS_BUCKET_NAME)

SUBTUPLE_DIR = os.path.join(MEDIA_ROOT, "subtuple")
SUBTUPLE_TMP_DIR = os.path.join(SUBTUPLE_DIR, "tmp")
ASSET_BUFFER_DIR = os.path.join(SUBTUPLE_DIR, "asset_buffer")

SITE_HOST = os.environ.get("SITE_HOST", f"substra-backend.{ORG_NAME}.xyz")
SITE_PORT = os.environ.get("SITE_PORT", DEFAULT_PORT)
DEFAULT_DOMAIN = os.environ.get("DEFAULT_DOMAIN", f"http://{SITE_HOST}:{SITE_PORT}")

CELERY_RESULT_BACKEND = "django-db"

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "libs.zxcvbn_validator.ZxcvbnValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 20,
        },
    },
    {"NAME": "libs.maximum_length_validator.MaximumLengthValidator", "OPTIONS": {"max_length": 64}},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CONTENT_DISPOSITION_HEADER = {
    "Content-Disposition": 'attachment; filename="API-response.json"',
}
