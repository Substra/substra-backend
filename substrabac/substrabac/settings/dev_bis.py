from .dev import *

# load org ledger conf
from substrabac.settings.conf.chunantes import org, peer, signcert

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
        'NAME': os.environ.get('SUBSTRABAC_DB_NAME', 'substrabac_bis'),
        'USER': os.environ.get('SUBSTRABAC_DB_USER', 'substrabac'),
        'PASSWORD': os.environ.get('SUBSTRABAC_DB_PWD', 'substrabac'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': 5432,
    }
}


MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'medias_bis')