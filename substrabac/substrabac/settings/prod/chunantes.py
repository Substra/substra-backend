from .__init__ import *

import os

org = [x for x in LEDGER_CONF['orgs'] if x['name'] == 'chu-nantes'][0]
orderer = LEDGER_CONF['orderers'][0]
peer = org['peers'][0]
signcert = org['users']['user']['home'] + '/msp/signcerts/cert.pem' # get owner which is the worker of the trainData

LEDGER = {
    'org': org,
    'peer': peer,
    'orderer': orderer,
    'signcert': signcert
}

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('SUBSTRABAC_CHU_NANTES_DB_NAME', 'substrabac_chunantes'),
        'USER': os.environ.get('SUBSTRABAC_DB_USER', 'substrabac'),
        'PASSWORD': os.environ.get('SUBSTRABAC_DB_PWD', 'substrabac'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': 5432,
    }
}

MEDIA_ROOT = '/substra/medias/chunantes'

SITE_ID = 1
SITE_HOST = os.environ.get('SITE_HOST', None)
SITE_PORT = os.environ.get('SITE_PORT', None)
