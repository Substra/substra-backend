import os
from datetime import timedelta

REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        #  'rest_framework.renderers.AdminRenderer',
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.authentication.SecureJWTAuthentication",  # for front/sdk/cli
        "libs.expiry_token_authentication.ExpiryTokenAuthentication",  # for front/sdk/cli
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "UNICODE_JSON": False,
    "ALLOWED_VERSIONS": ("0.0",),
    "DEFAULT_VERSION": "0.0",
    "EXCEPTION_HANDLER": "api.views.exception_handler.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": f'{os.environ.get("DEFAULT_THROTTLE_RATES", 40)}/minute',
        "login": f'{os.environ.get("DEFAULT_THROTTLE_RATES", 40)}/minute',
    },
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "libs.json_multipart_parser.JsonMultiPartParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_LIFETIME", 24 * 60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("REFRESH_TOKEN_LIFETIME", 24 * 60 * 7))),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("JWT",),
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
}
