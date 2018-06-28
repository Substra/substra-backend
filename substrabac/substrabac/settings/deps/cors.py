# encoding: utf-8

from __future__ import unicode_literals, absolute_import
from .. import common

common.INSTALLED_APPS += (
    'corsheaders',
)

common.MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
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
