from .common import *
from .deps.cors import *
from .deps.restframework import *
import tempfile

import logging
logging.disable(logging.CRITICAL)

ORG_NAME = 'OrgTestSuite'
DEFAULT_DOMAIN = 'http://testserver'

ASSET_BUFFER_DIR = tempfile.mkdtemp()  # overridden in individual tests

ORCHESTRATOR_HOST = "orchestrator"
ORCHESTRATOR_PORT = 9000
ORCHESTRATOR_TLS_ENABLED = False
ORCHESTRATOR_MTLS_ENABLED = False

ORCHESTRATOR_RABBITMQ_HOST = "rabbit"
ORCHESTRATOR_RABBITMQ_PORT = 5672
ORCHESTRATOR_RABBITMQ_AUTH_USER = "user"
ORCHESTRATOR_RABBITMQ_AUTH_PASSWORD = "password"
ORCHESTRATOR_RABBITMQ_TLS_ENABLED = False

LEDGER_MSP_ID = 'testOrgMSP'
