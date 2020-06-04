# encoding: utf-8

from __future__ import unicode_literals, absolute_import
import os
import json
from .. import common

common.INSTALLED_APPS += (
    'corsheaders',
)

common.MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

CORS_ORIGIN_WHITELIST = json.loads(os.environ.get('CORS_ORIGIN_WHITELIST', "[]"))
CORS_ORIGIN_ALLOW_ALL = False if CORS_ORIGIN_WHITELIST else True
CORS_ALLOW_CREDENTIALS = common.to_bool(os.environ.get('CORS_ALLOW_CREDENTIALS', False))
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'token',
)
