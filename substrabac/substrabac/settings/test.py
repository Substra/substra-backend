from .common import *  # noqa

from .deps.restframework import *  # noqa
from .deps.cors import *  # noqa

import logging
logging.disable(logging.CRITICAL)

REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = []
