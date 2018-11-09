from ..common import *

from ..deps.restframework import *
from ..deps.cors import *
from ..deps.raven import *

DEBUG = False
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
os.environ['HTTPS'] = "on"
os.environ['wsgi.url_scheme'] = 'https'  # safer

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
        # 'error_file': {
        #     'class': 'logging.FileHandler',
        #     'formatter': 'generic',
        #     'filename': '/var/log/substrabac.error.log',
        # },
        # 'access_file': {
        #     'class': 'logging.FileHandler',
        #     'formatter': 'generic',
        #     'filename': '/var/log/substrabac.access.log',
        # },
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

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'statics')

# deactivate when public
BASICAUTH_USERNAME = os.environ.get('AUTH_USER', '')
BASICAUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')
MIDDLEWARE += ['libs.BasicAuthMiddleware.BasicAuthMiddleware']
