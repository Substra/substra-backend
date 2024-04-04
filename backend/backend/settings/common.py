"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import json
import os
import secrets

import structlog
from django.core.files.storage import FileSystemStorage

from .deps.celery import *
from .deps.jwt import *
from .deps.org import *
from .deps.path import *
from .deps.utils import to_bool

DEBUG = False


SUBPATH = os.environ.get("SUBPATH", "")  # prefix for backend endpoints
if SUBPATH:
    SUBPATH = SUBPATH.strip("/") + "/"

ALLOWED_HOSTS = ["127.0.0.1", "::1", "localhost"] + json.loads(os.environ.get("ALLOWED_HOSTS", "[]"))
if os.environ.get("HOST_IP"):
    ALLOWED_HOSTS.append(os.environ.get("HOST_IP"))
if os.environ.get("POD_IP"):
    ALLOWED_HOSTS.append(os.environ.get("POD_IP"))


SECRET_KEY = os.environ.get(
    "SECRET_KEY", secrets.token_urlsafe()  # token_urlsafe uses a "reasonable default" length
)  # built in Django, but also used for signing JWTs

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_celery_results",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "substrapp",
    "organization",
    "users",
    "api",
    "drf_spectacular",
    "django_filters",
    "django_structlog",
    "builder",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "organization.authentication.OrganizationBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.RemoteUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "libs.health_check_middleware.HealthCheckMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
]

DJANGO_STRUCTLOG_CELERY_ENABLED = True

DJANGO_LOG_SQL_QUERIES = to_bool(os.environ.get("DJANGO_LOG_SQL_QUERIES", "True"))
if DJANGO_LOG_SQL_QUERIES:
    MIDDLEWARE.append("libs.sql_printing_middleware.SQLPrintingMiddleware")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
# @CSRF_TRUSTED_ORIGINS: A list of origins that are allowed to use unsafe HTTP methods
CSRF_TRUSTED_ORIGINS = json.loads(os.environ.get("CSRF_TRUSTED_ORIGINS", "[]"))

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_DATABASE", f"backend_{ORG_NAME}"),
        "USER": os.environ.get("DATABASE_USERNAME", "backend"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "backend"),
        "HOST": os.environ.get("DATABASE_HOSTNAME", "localhost"),
        "PORT": int(os.environ.get("DATABASE_PORT", "5432")),
    }
}

DATASAMPLE_STORAGE = FileSystemStorage()
MODEL_STORAGE = FileSystemStorage()
FUNCTION_STORAGE = FileSystemStorage()
DATAMANAGER_STORAGE = FileSystemStorage()
METRICS_STORAGE = FileSystemStorage()
ASSET_LOGS_STORAGE = FileSystemStorage()

OBJECTSTORE_URL = os.environ.get("OBJECTSTORE_URL")
OBJECTSTORE_ACCESSKEY = os.environ.get("OBJECTSTORE_ACCESSKEY")
OBJECTSTORE_SECRETKEY = os.environ.get("OBJECTSTORE_SECRETKEY")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/django_cache",  # nosec
    }
}

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
            "min_length": 9,
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

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = f"/{SUBPATH}static/"
MEDIA_ROOT = PROJECT_ROOT / "medias"
SITE_ID = 1

TASK = {
    "CACHE_DOCKER_IMAGES": to_bool(os.environ.get("TASK_CACHE_DOCKER_IMAGES", False)),
    "CHAINKEYS_ENABLED": to_bool(os.environ.get("TASK_CHAINKEYS_ENABLED", False)),
    "LIST_WORKSPACE": to_bool(os.environ.get("TASK_LIST_WORKSPACE", True)),
    "KANIKO_MIRROR": to_bool(os.environ.get("KANIKO_MIRROR", False)),
    "KANIKO_IMAGE": os.environ.get("KANIKO_IMAGE"),
    "KANIKO_DOCKER_CONFIG_SECRET_NAME": os.environ.get("KANIKO_DOCKER_CONFIG_SECRET_NAME"),
    "COMPUTE_POD_STARTUP_TIMEOUT_SECONDS": int(os.environ.get("COMPUTE_POD_STARTUP_TIMEOUT_SECONDS", 300)),
    "PRIVATE_CA_ENABLED": to_bool(os.environ.get("PRIVATE_CA_ENABLED")),
    "PRIVATE_CA_CONFIGMAP_NAME": os.environ.get("PRIVATE_CA_CONFIGMAP_NAME"),
    "PRIVATE_CA_FILENAME": os.environ.get("PRIVATE_CA_FILENAME"),
}

WORKER_PVC_IS_HOSTPATH = to_bool(os.environ.get("WORKER_PVC_IS_HOSTPATH"))
WORKER_PVC_DOCKER_CACHE = os.environ.get("WORKER_PVC_DOCKER_CACHE")
WORKER_PVC_SUBTUPLE = os.environ.get("WORKER_PVC_SUBTUPLE")
WORKER_REPLICA_SET_NAME = os.environ.get("WORKER_REPLICA_SET_NAME")

NAMESPACE = os.getenv("NAMESPACE")
HOSTNAME = os.getenv("HOSTNAME")

# Used by the Secure aggregation mechanism to retrieve chainkeys
K8S_SECRET_NAMESPACE = os.getenv("K8S_SECRET_NAMESPACE", "default")

REGISTRY = os.getenv("REGISTRY", "")
REGISTRY_SCHEME = os.getenv("REGISTRY_SCHEME")
REGISTRY_PULL_DOMAIN = os.getenv("REGISTRY_PULL_DOMAIN")
REGISTRY_IS_LOCAL = to_bool(os.environ.get("REGISTRY_IS_LOCAL"))
REGISTRY_SERVICE_NAME = os.environ.get("REGISTRY_SERVICE_NAME")

COMPUTE_POD_RUN_AS_USER = os.environ.get("COMPUTE_POD_RUN_AS_USER")
COMPUTE_POD_RUN_AS_GROUP = os.environ.get("COMPUTE_POD_RUN_AS_GROUP")
COMPUTE_POD_FS_GROUP = os.environ.get("COMPUTE_POD_FS_GROUP")
COMPUTE_POD_GKE_GPUS_LIMITS = int(os.environ.get("COMPUTE_POD_GKE_GPUS_LIMITS", 0))

# Prometheus configuration
ENABLE_METRICS = to_bool(os.environ.get("ENABLE_METRICS", False))
# Keeping migrations enabled leads to issues with collectsatic
PROMETHEUS_EXPORT_MIGRATIONS = False
if ENABLE_METRICS:
    # Enable tasks related events so that tasks can be monitored
    CELERY_WORKER_SEND_TASK_EVENTS = True
    CELERY_TASK_SEND_SENT_EVENT = True

    INSTALLED_APPS.append("django_prometheus")
    MIDDLEWARE = (
        ["django_prometheus.middleware.PrometheusBeforeMiddleware"]
        + MIDDLEWARE
        + ["django_prometheus.middleware.PrometheusAfterMiddleware"]
    )

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Uploaded file max size, in bytes
DATA_UPLOAD_MAX_SIZE = int(os.environ.get("DATA_UPLOAD_MAX_SIZE", 1024 * 1024 * 1024))  # bytes


GZIP_MODELS = to_bool(os.environ.get("GZIP_MODELS", False))

HTTP_CLIENT_TIMEOUT_SECONDS = int(os.environ.get("HTTP_CLIENT_TIMEOUT_SECONDS", 30))

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOGGING_USE_COLORS = to_bool(os.environ.get("LOGGING_USE_COLORS", True))

DEBUG_KEEP_POD_AND_DIRS = to_bool(os.environ.get("DEBUG_KEEP_POD_AND_DIRS", False))

PAGINATION_MAX_PAGE_SIZE = int(os.environ.get("PAGINATION_MAX_PAGE_SIZE", 10000))

pre_chain = [
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
]
ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS = to_bool(os.environ.get("ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS", False))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": pre_chain,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "key_value",
        },
    },
    "loggers": {
        # root logger
        "": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": True,
        },
        # django and its applications
        "django": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "substrapp": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "api": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "events": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "builder": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        # third-party libraries
        "celery": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": True,
        },
    },
}

BACKEND_VERSION = os.environ.get("BACKEND_VERSION", "dev")

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

COMMON_HOST_DOMAIN = os.environ.get("COMMON_HOST_DOMAIN")

ISOLATED = to_bool(os.environ.get("ISOLATED"))

CONTENT_DISPOSITION_HEADER = {}

VIRTUAL_USERNAMES = {
    # Username of additional Django user representing user external to organization
    "EXTERNAL": "external",
    # Username of additional Django user representing deleted user to not break FK references
    "DELETED": "deleted",
}
