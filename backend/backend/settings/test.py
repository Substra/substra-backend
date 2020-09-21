from .common import *
from .deps.cors import *
from .deps.restframework import *

import logging
logging.disable(logging.CRITICAL)

LEDGER_CALL_RETRY = False
ORG_NAME = 'OrgTestSuite'
