from .__init__ import *

import os

org = LEDGER_CONF['orgs']['owkin']
peer = org['peers'][0]

# get owner which is the worker of the trainData
signcert = '/substra/data/orgs/owkin/user/msp/signcerts/cert.pem'

LEDGER = {
    'org': org,
    'peer': peer,
    'signcert': signcert
}

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('SUBSTRABAC_OWKIN_DB_NAME', 'substrabac_owkin'),
        'USER': os.environ.get('SUBSTRABAC_DB_USER', 'substrabac'),
        'PASSWORD': os.environ.get('SUBSTRABAC_DB_PWD', 'substrabac'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': 5432,
    }
}

MEDIA_ROOT = '/substra/medias/owkin'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'statics')

SITE_ID = 1
SITE_HOST = os.environ.get('SITE_HOST', 'owkin.substrabac')
SITE_PORT = os.environ.get('SITE_PORT', '8000')
