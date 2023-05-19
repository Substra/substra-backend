import logging
import tempfile

from .common import *
from .deps.cors import *
from .deps.oidc import *
from .deps.restframework import *

logging.disable(logging.CRITICAL)

ORG_NAME = "OrgTestSuite"
DEFAULT_DOMAIN = "http://testserver"
ALLOWED_HOSTS = ["testserver"]

ASSET_BUFFER_DIR = tempfile.mkdtemp()  # overridden in individual tests
SUBTUPLE_DIR = os.path.join(MEDIA_ROOT, "subtuple")
SUBTUPLE_TMP_DIR = os.path.join(SUBTUPLE_DIR, "tmp")

ORCHESTRATOR_HOST = "orchestrator"
ORCHESTRATOR_PORT = 9000
ORCHESTRATOR_TLS_ENABLED = False
ORCHESTRATOR_MTLS_ENABLED = False
ORCHESTRATOR_RETRY_DELAY = 0
ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS = 60000
ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS = 20000
ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS = False
ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA = 0

LEDGER_MSP_ID = "testOrgMSP"
LEDGER_CHANNELS = {"mychannel": {"chaincode": {"name": "mycc"}}}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRESQL_DATABASE", "substra"),
        "USER": os.environ.get("POSTGRESQL_USERNAME", "postgres"),
        "PASSWORD": os.environ.get("POSTGRESQL_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRESQL_HOSTNAME", "localhost"),
        "PORT": int(os.environ.get("POSTGRESQL_PORT", 5432)),
    }
}
