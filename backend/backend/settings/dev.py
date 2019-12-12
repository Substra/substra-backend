import os

from .common import *
from .deps.cors import *
from .deps.org import *
from .deps.restframework import *

DEBUG = True
# LEDGER_CALL_RETRY = False  # uncomment to overwrite the ledger setting value

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get(f'BACKEND_DB_NAME', f'backend_{ORG_NAME}'),
        'USER': os.environ.get('BACKEND_DB_USER', 'backend'),
        'PASSWORD': os.environ.get('BACKEND_DB_PWD', 'backend'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': 5432,
    }
}

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(PROJECT_ROOT, f'medias/{ORG_NAME}'))

SITE_HOST = f'substra-backend.{ORG_NAME}.xyz'
SITE_PORT = DEFAULT_PORT
DEFAULT_DOMAIN = os.environ.get('DEFAULT_DOMAIN', f'http://{SITE_HOST}:{SITE_PORT}')
CELERY_TASK_RETRY_DELAY_SECONDS = 0

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'error_file': {
            'level': 'INFO',
            'filename': os.path.join(PROJECT_ROOT, 'backend.log'),
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'events': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
