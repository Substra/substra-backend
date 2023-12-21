import logging
import tempfile

from .common import *
from .deps.image_build import *
from .deps.restframework import *
from .mods.cors import *
from .mods.oidc import *

logging.disable(logging.CRITICAL)

DEBUG = True

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

MSP_ID = "testOrgMSP"
CHANNELS = {"mychannel": {"model_export_enabled": False}}
