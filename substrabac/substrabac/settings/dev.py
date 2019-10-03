import os

from .common import *
from .deps.cors import *
from .deps.org import *
from .deps.ledger import *
from .deps.restframework import *


BASICAUTH_USERNAME = os.environ.get('BACK_AUTH_USER', 'dev')
BASICAUTH_PASSWORD = os.environ.get('BACK_AUTH_PASSWORD', 'dev')

DEBUG = True

TASK = {
    'CAPTURE_LOGS': to_bool(os.environ.get('TASK_CAPTURE_LOGS', True)),
    'CLEAN_EXECUTION_ENVIRONMENT': to_bool(os.environ.get('TASK_CLEAN_EXECUTION_ENVIRONMENT', True)),
    'CACHE_DOCKER_IMAGES': to_bool(os.environ.get('TASK_CACHE_DOCKER_IMAGES', False)),
}

LEDGER_CALL_RETRY = False  # Overwrite the ledger setting value

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get(f'SUBSTRABAC_{ORG_DB_NAME}_DB_NAME', f'substrabac_{ORG_NAME}'),
        'USER': os.environ.get('SUBSTRABAC_DB_USER', 'substrabac'),
        'PASSWORD': os.environ.get('SUBSTRABAC_DB_PWD', 'substrabac'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': 5432,
    }
}

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(PROJECT_ROOT, f'medias/{ORG_NAME}'))

DEFAULT_DOMAIN = os.environ.get('DEFAULT_DOMAIN', f'http://substrabac.{ORG_NAME}.com:{DEFAULT_PORT}')

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
            'filename': os.path.join(PROJECT_ROOT, 'substrabac.log'),
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
