"""
Add Cross-origin site requests (CORS) restrictions
"""

import json
import os

from .. import common
from ..deps.utils import to_bool

common.INSTALLED_APPS += ("corsheaders",)

common.MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

# @CORS_ORIGIN_WHITELIST: A list of origins that are authorized to make cross-site HTTP requests (e.g.the frontend url).
CORS_ALLOWED_ORIGINS = json.loads(os.environ.get("CORS_ORIGIN_WHITELIST", "[]"))
CORS_ALLOW_ALL_ORIGINS = False
# @CORS_ALLOW_CREDENTIALS: If True cookies can be included in cross site requests. Set this to `True` for frontend auth.
CORS_ALLOW_CREDENTIALS = to_bool(os.environ.get("CORS_ALLOW_CREDENTIALS", False))
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "token",
)
