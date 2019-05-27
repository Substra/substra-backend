import os
import asyncio
import glob
import json

from .common import *

from .deps.restframework import *
from .deps.cors import *
from .deps.raven import *

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore


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

HLF_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(HLF_LOOP)

channel_name = LEDGER['channel_name']
chaincode_name = LEDGER['chaincode_name']
peer = LEDGER['peer']
peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]
orderer = LEDGER['orderer']

requestor_config = LEDGER['client']

CLIENT = Client()
CLIENT.new_channel(channel_name)

REQUESTOR = create_user(name=requestor_config['name'],
                        org=requestor_config['org'],
                        state_store=FileKeyValueStore(requestor_config['state_store']),
                        msp_id=requestor_config['msp_id'],
                        key_path=glob.glob(requestor_config['key_path'])[0],
                        cert_path=requestor_config['cert_path'])

target_peer = Peer(name=peer['name'])

# Need loop
target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer_port}',
                              'grpcOptions': peer['grpcOptions'],
                              'tlsCACerts': {'path': peer['tlsCACerts']},
                              'clientKey': {'path': peer['clientKey']},
                              'clientCert': {'path': peer['clientCert']},
                              })
CLIENT._peers[peer['name']] = target_peer

target_orderer = Orderer(name=orderer['name'])

# Need loop
target_orderer.init_with_bundle({'url': f'{orderer["host"]}:{orderer["port"]}',
                                 'grpcOptions': orderer['grpcOptions'],
                                 'tlsCACerts': {'path': orderer['ca']},
                                 'clientKey': {'path': peer['clientKey']},  # use peer creds (mutual tls)
                                 'clientCert': {'path': peer['clientCert']},  # use peer creds (mutual tls)
                                 })
CLIENT._orderers[orderer['name']] = target_orderer

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

DEFAULT_DOMAIN = os.environ.get('DEFAULT_DOMAIN', f'http://{SITE_HOST}:{SITE_PORT}')

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
