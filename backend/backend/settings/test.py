from .common import *
from .deps.cors import *
from .deps.restframework import *
import tempfile

import logging
logging.disable(logging.CRITICAL)

ORG_NAME = 'OrgTestSuite'
LEDGER_SYNC_ENABLED = True
ASSET_BUFFER_DIR = tempfile.mkdtemp()  # overridden in individual tests
