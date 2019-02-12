from .__init__ import *

import os

LEDGER = json.load(open('/substra/conf/owkin/substrabac/conf.json', 'r'))

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

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(PROJECT_ROOT, 'medias/owkin'))

SITE_ID = 1
SITE_HOST = 'owkin.substrabac'
SITE_PORT = '8000'
