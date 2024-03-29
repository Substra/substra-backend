import os
from datetime import timedelta

from .utils import to_bool

REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        #  'rest_framework.renderers.AdminRenderer',
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.authentication.SecureJWTAuthentication",  # JWT for front
        "users.authentication.BearerTokenAuthentication",  # Bearer token for SDK
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "libs.permissions.IsAuthorized",
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

SPECTACULAR_SETTINGS = {
    "SERVE_PERMISSIONS": ["libs.permissions.IsAuthorized"],
}

EXPIRY_TOKEN_LIFETIME = timedelta(minutes=int(os.environ.get("EXPIRY_TOKEN_LIFETIME", 24 * 60)))  # minutes
EXPIRY_TOKEN_ENABLED = to_bool(os.environ.get("EXPIRY_TOKEN_ENABLED", True))
if EXPIRY_TOKEN_ENABLED:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "users.authentication.ImplicitBearerTokenAuthentication"
    ] + REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
    # Legacy Bearer token for api-token-auth/
    # must be loaded BEFORE BearerTokenAuthentication
