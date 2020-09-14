import os

from .common import *
from .deps.cors import *
from .deps.org import *
from .deps.restframework import *


DEBUG = False

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
os.environ['HTTPS'] = "on"
os.environ['wsgi.url_scheme'] = 'https'

SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 365 * 24 * 3600))  # 1 year
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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

CELERY_RESULT_BACKEND = 'django-db'

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
            'min_length': 20,
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

