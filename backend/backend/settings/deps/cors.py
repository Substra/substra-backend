import json
import os

from .. import common

common.INSTALLED_APPS += ("corsheaders",)

common.MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

CORS_ALLOWED_ORIGINS = json.loads(os.environ.get("CORS_ORIGIN_WHITELIST", "[]"))
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = common.to_bool(os.environ.get("CORS_ALLOW_CREDENTIALS", False))
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
