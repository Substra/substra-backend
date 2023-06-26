import os

from substrapp.storages.minio import MinioStorage

from .common import *
from .deps.ledger import *
from .deps.org import *
from .deps.restframework import *
from .mods.cors import *
from .mods.oidc import *

DEBUG = True

STATIC_ROOT = BASE_DIR / "statics"

# Enable Browsable API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += ("rest_framework.renderers.BrowsableAPIRenderer",)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
    "libs.session_authentication.CustomSessionAuthentication",
]

DATASAMPLE_BUCKET_NAME = "substra-datasample"
DATASAMPLE_STORAGE = MinioStorage(DATASAMPLE_BUCKET_NAME)

MODEL_BUCKET_NAME = "substra-model"
MODEL_STORAGE = MinioStorage(MODEL_BUCKET_NAME)

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(PROJECT_ROOT / "medias" / ORG_NAME))
SERVERMEDIAS_ROOT = os.environ.get("SERVERMEDIAS_ROOT", str(PROJECT_ROOT / "servermedias" / ORG_NAME))
FUNCTION_BUCKET_NAME = "substra-function"
FUNCTION_STORAGE = MinioStorage(FUNCTION_BUCKET_NAME)

DATAMANAGER_BUCKET_NAME = "substra-datamanager"
DATAMANAGER_STORAGE = MinioStorage(DATAMANAGER_BUCKET_NAME)

COMPUTE_TASK_LOGS_BUCKET_NAME = "substra-compute-task-logs"
COMPUTE_TASK_LOGS_STORAGE = MinioStorage(COMPUTE_TASK_LOGS_BUCKET_NAME)

SUBTUPLE_DIR = os.path.join(MEDIA_ROOT, "subtuple")
SUBTUPLE_TMP_DIR = os.path.join(SUBTUPLE_DIR, "tmp")
ASSET_BUFFER_DIR = os.path.join(SUBTUPLE_DIR, "asset_buffer")

SITE_HOST = f"substra-backend.{ORG_NAME}.xyz"
SITE_PORT = DEFAULT_PORT
DEFAULT_DOMAIN = os.environ.get("DEFAULT_DOMAIN", f"http://{SITE_HOST}:{SITE_PORT}")

CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_MAX_RETRIES = int(os.environ.get("CELERY_TASK_MAX_RETRIES", 0))
