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

CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_MAX_RETRIES = 1 # 1 retry == 2 attempts
CELERY_TASK_RETRY_DELAY_SECONDS = 0

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s - %(asctime)s - %(name)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        # root logger
        '': {
            'level': 'WARNING',
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
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'events': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        # third-party libraries
        'hfc': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
        'celery': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}
