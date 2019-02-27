import os

from .common import *

from .deps.restframework import *
from .deps.cors import *
from .deps.raven import *

DEBUG = False
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
os.environ['HTTPS'] = "on"
os.environ['wsgi.url_scheme'] = 'https'  # safer

import os

ORG = os.environ.get('SUBSTRABAC_ORG', 'substra')
DEFAULT_PORT = os.environ.get('SUBSTRABAC_DEFAULT_PORT', '8000')

ORG_NAME = ORG.replace('-', '')
ORG_DB_NAME = ORG.replace('-', '_').upper()

LEDGER = json.load(open(f'/substra/conf/{ORG}/substrabac/conf.json', 'r'))

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

MEDIA_ROOT = f'/substra/medias/{ORG_NAME}'
DRYRUN_ROOT = f'/substra/dryrun/{ORG}'

SITE_ID = 1
SITE_HOST = os.environ.get('SITE_HOST', f'{ORG_NAME}.substrabac')
SITE_PORT = os.environ.get('SITE_PORT', DEFAULT_PORT)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'statics')

# deactivate when public
BASICAUTH_USERNAME = os.environ.get('BACK_AUTH_USER', None)
BASICAUTH_PASSWORD = os.environ.get('BACK_AUTH_PASSWORD', None)
MIDDLEWARE += ['libs.BasicAuthMiddleware.BasicAuthMiddleware']


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
            'filename': '/var/log/substrabac.error.log',
        },
        'access_file': {
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': '/var/log/substrabac.access.log',
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
