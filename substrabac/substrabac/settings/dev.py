import os
import asyncio
import glob
import json

from .common import *

from .deps.restframework import *
from .deps.cors import *

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore


DEBUG = True

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

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(PROJECT_ROOT, f'medias/{ORG_NAME}'))
DRYRUN_ROOT = os.environ.get('DRYRUN_ROOT', os.path.join(PROJECT_ROOT, f'dryrun/{ORG}'))

if not os.path.exists(DRYRUN_ROOT):
    os.makedirs(DRYRUN_ROOT, exist_ok=True)

SITE_ID = 1
SITE_HOST = f'{ORG_NAME}.substrabac'
SITE_PORT = DEFAULT_PORT

DEFAULT_DOMAIN = os.environ.get('DEFAULT_DOMAIN', f'http://{SITE_HOST}:{SITE_PORT}')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'error_file': {
            'level': 'INFO',
            'filename': os.path.join(PROJECT_ROOT, 'substrabac.log'),
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
