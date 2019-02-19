from .__init__ import *

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

SITE_ID = 1
SITE_HOST = os.environ.get('SITE_HOST', f'{ORG_NAME}.substrabac')
SITE_PORT = os.environ.get('SITE_PORT', DEFAULT_PORT)
