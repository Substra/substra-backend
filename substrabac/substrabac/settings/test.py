from .common import *
from .deps.cors import *
from .deps.restframework import *

import logging
logging.disable(logging.CRITICAL)

BASICAUTH_USERNAME = "test"
BASICAUTH_PASSWORD = "test"

# by default, bypass basic auth
BASIC_AUTHENTICATION_MODULE = 'substrapp.views.utils'
