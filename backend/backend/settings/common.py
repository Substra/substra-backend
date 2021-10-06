"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sys
import json
from datetime import timedelta
import structlog

from libs.gen_secret_key import write_secret_key


TRUE_VALUES = {
    't', 'T',
    'y', 'Y', 'yes', 'YES',
    'true', 'True', 'TRUE',
    'on', 'On', 'ON',
    '1', 1,
    True
}


def to_bool(value):
    return value in TRUE_VALUES


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.normpath(os.path.join(PROJECT_ROOT, 'libs')))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_FILE = os.path.normpath(os.path.join(PROJECT_ROOT, 'SECRET'))

# KEY CONFIGURATION
# Try to load the SECRET_KEY from our SECRET_FILE. If that fails, then generate
# a random SECRET_KEY and save it into our SECRET_FILE for future loading. If
# everything fails, then just raise an exception.
try:
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        SECRET_KEY = write_secret_key(SECRET_FILE)
    except IOError:
        raise Exception(f'Cannot open file `{SECRET_FILE}` for writing.')
# END KEY CONFIGURATION

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '::1', 'localhost'] + json.loads(os.environ.get('ALLOWED_HOSTS', "[]"))
if os.environ.get('HOST_IP'):
    ALLOWED_HOSTS.append(os.environ.get('HOST_IP'))
if os.environ.get('POD_IP'):
    ALLOWED_HOSTS.append(os.environ.get('POD_IP'))

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_celery_results',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'substrapp',
    'node',
    'users',
    'drf_spectacular',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'node.authentication.NodeBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'libs.health_check_middleware.HealthCheckMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'django_structlog.middlewares.CeleryMiddleware',
]


DJANGO_LOG_SQL_QUERIES = to_bool(os.environ.get('DJANGO_LOG_SQL_QUERIES', 'True'))
if DJANGO_LOG_SQL_QUERIES:
    MIDDLEWARE.append(
        'libs.sql_printing_middleware.SQLPrintingMiddleware'
    )

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite3'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'libs.zxcvbn_validator.ZxcvbnValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'libs.maximum_length_validator.MaximumLengthValidator',
        'OPTIONS': {
            'max_length': 64
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'medias')
MEDIA_URL = '/media/'

SITE_ID = 1

TASK = {
    'CACHE_DOCKER_IMAGES': to_bool(os.environ.get('TASK_CACHE_DOCKER_IMAGES', False)),
    'CHAINKEYS_ENABLED': to_bool(os.environ.get('TASK_CHAINKEYS_ENABLED', False)),
    'LIST_WORKSPACE': to_bool(os.environ.get('TASK_LIST_WORKSPACE', True)),
    'KANIKO_MIRROR': to_bool(os.environ.get('KANIKO_MIRROR', False)),
    'KANIKO_IMAGE': os.environ.get('KANIKO_IMAGE'),
    'KANIKO_DOCKER_CONFIG_SECRET_NAME': os.environ.get('KANIKO_DOCKER_CONFIG_SECRET_NAME'),
    'COMPUTE_REGISTRY': os.environ.get('COMPUTE_REGISTRY'),
    'COMPUTE_POD_STARTUP_TIMEOUT_SECONDS': int(os.environ.get('COMPUTE_POD_STARTUP_TIMEOUT_SECONDS', 300)),
}

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True  # since 4.0
CELERY_TASK_MAX_RETRIES = 5
CELERY_TASK_RETRY_DELAY_SECONDS = 2
CELERY_WORKER_CONCURRENCY = int(os.environ.get('CELERY_WORKER_CONCURRENCY', 1))
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://localhost:5672//')

K8S_PVC = {env_key: env_value for env_key, env_value in os.environ.items() if "_PVC" in env_key}

NAMESPACE = os.getenv("NAMESPACE")

REGISTRY = os.getenv("REGISTRY")
REGISTRY_SCHEME = os.getenv("REGISTRY_SCHEME")
REGISTRY_PULL_DOMAIN = os.getenv("REGISTRY_PULL_DOMAIN")
REGISTRY_IS_LOCAL = to_bool(os.environ.get('REGISTRY_IS_LOCAL'))
REGISTRY_SERVICE_NAME = os.environ.get('REGISTRY_SERVICE_NAME')

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

EXPIRY_TOKEN_LIFETIME = timedelta(minutes=int(os.environ.get('EXPIRY_TOKEN_LIFETIME', 24 * 60)))
TOKEN_STRATEGY = os.environ.get('TOKEN_STRATEGY', 'unique')

GZIP_MODELS = to_bool(os.environ.get('GZIP_MODELS', False))

HTTP_CLIENT_TIMEOUT_SECONDS = int(os.environ.get('HTTP_CLIENT_TIMEOUT_SECONDS', 30))

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOGGING_USE_COLORS = to_bool(os.environ.get('LOGGING_USE_COLORS', True))

# With DEBUG_QUICK_IMAGE, container images are never deleted, and image names are based on the algo/metrics checksum
# (instead of algo/metrics key, without the option). This allows reuse of images and significantly speeds up end-to-end
# tests.
DEBUG_QUICK_IMAGE = to_bool(os.environ.get('DEBUG_QUICK_IMAGE', False))
DEBUG_KEEP_POD_AND_DIRS = to_bool(os.environ.get('DEBUG_KEEP_POD_AND_DIRS', False))

PAGINATION_MAX_PAGE_SIZE = int(os.environ.get('PAGINATION_MAX_PAGE_SIZE', 100))

pre_chain = [
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(key_order=['timestamp', 'level', 'logger', 'event']),
            "foreign_pre_chain": pre_chain,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'key_value',
        },
    },
    'loggers': {
        # root logger
        '': {
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'handlers': ['console'],
            'propagate': True,
        },
        # django and its applications
        'django': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'substrapp': {
            'level': LOG_LEVEL,
            'handlers': ['console'],
            'propagate': False,
        },
        'events': {
            'level': LOG_LEVEL,
            'handlers': ['console'],
            'propagate': False,
        },
        # third-party libraries
        'celery': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
        },
        'kubernetes.client.rest': { # This is too verbose in debug level
            'level': 'INFO' if DEBUG else 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

BACKEND_VERSION = os.environ.get('BACKEND_VERSION')

structlog.configure(
    processors=[
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
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

COMMON_HOST_DOMAIN = os.environ.get('COMMON_HOST_DOMAIN')
