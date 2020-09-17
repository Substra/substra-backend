import os

from .common import *
from .deps.cors import *
from .deps.org import *
from .deps.restframework import *

DEBUG = True
# LEDGER_CALL_RETRY = False  # uncomment to overwrite the ledger setting value

# Enable Browsable API
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += (
    'rest_framework.renderers.BrowsableAPIRenderer',
)
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
    'libs.session_authentication.CustomSessionAuthentication',
]

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
CELERY_TASK_MAX_RETRIES = 0
CELERY_TASK_RETRY_DELAY_SECONDS = 0
