import os

from .common import *
from .deps.cors import *
from .deps.raven import *
from .deps.org import *
from .deps.restframework import *


DEBUG = False

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
os.environ['HTTPS'] = "on"
os.environ['wsgi.url_scheme'] = 'https'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'statics')

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

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', f'/substra/medias/{ORG_NAME}')

SITE_HOST = os.environ.get('SITE_HOST', f'substra-backend.{ORG_NAME}.xyz')
SITE_PORT = os.environ.get('SITE_PORT', DEFAULT_PORT)
DEFAULT_DOMAIN = os.environ.get('DEFAULT_DOMAIN', f'http://{SITE_HOST}:{SITE_PORT}')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            '()': 'logging.Formatter',
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': '/var/log/substra-backend.error.log',
        },
        'access_file': {
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': '/var/log/substra-backend.access.log',
        },
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        }
    },
}
