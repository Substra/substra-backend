import os
from datetime import timedelta

REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        #  'rest_framework.renderers.AdminRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.SecureJWTAuthentication',  # for front/sdk/cli
        'libs.expiryTokenAuthentication.ExpiryTokenAuthentication',  # for front/sdk/cli
        'libs.sessionAuthentication.CustomSessionAuthentication',  # for web browsable api
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'UNICODE_JSON': False,
    'DEFAULT_VERSIONING_CLASS': 'libs.versioning.AcceptHeaderVersioningRequired',
    'ALLOWED_VERSIONS': ('0.0',),
    'DEFAULT_VERSION': '0.0',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('ACCESS_TOKEN_LIFETIME', 24*60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('REFRESH_TOKEN_LIFETIME', 24*60*7))),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('JWT',),
}
