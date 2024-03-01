"""
OpenID Connect (for SSO)
"""

import logging
import os

import requests

from .. import common
from ..deps import ledger
from ..deps.utils import to_bool

_LOGGER = logging.getLogger(__name__)

# mozilla-django-oidc values are OIDC_*
# but to avoid polluting the global namespace
# we'll use an "OIDC" dict for any setting added by us

OIDC = {
    "ENABLED": to_bool(os.environ.get("OIDC_ENABLED", "false")),
    "USERS": {},
    "OP": {},
}

if OIDC["ENABLED"]:  # noqa: C901
    # Reusing name from Mozilla OIDC
    OIDC_TIMEOUT = os.environ.get("OIDC_TIMEOUT", common.HTTP_CLIENT_TIMEOUT_SECONDS)

    common.INSTALLED_APPS += ["mozilla_django_oidc"]  # load after auth
    common.AUTHENTICATION_BACKENDS += ["users.authentication.OIDCAuthenticationBackend"]
    common.LOGGING["loggers"]["mozilla_django_oidc"] = {
        "level": common.LOG_LEVEL,
        "handlers": ["console"],
        "propagate": False,
    }

    OIDC["USERS"]["APPEND_DOMAIN"] = to_bool(os.environ.get("OIDC_USERS_APPEND_DOMAIN", "false"))

    OIDC["USERS"]["DEFAULT_CHANNEL"] = os.environ.get("OIDC_USERS_DEFAULT_CHANNEL")
    OIDC["USERS"]["MUST_BE_APPROVED"] = to_bool(os.environ.get("OIDC_USERS_MUST_BE_APPROVED", "false"))
    if OIDC["USERS"]["DEFAULT_CHANNEL"] and OIDC["USERS"]["MUST_BE_APPROVED"]:
        raise Exception("Both 'default channel' and 'user must be approved' options are activated")
    if not (OIDC["USERS"]["DEFAULT_CHANNEL"] or OIDC["USERS"]["MUST_BE_APPROVED"]):
        raise Exception(
            "At least one option between 'default channel' and 'user must be approved' needs to be activated"
        )
    OIDC["USERS"]["LOGIN_VALIDITY_DURATION"] = int(
        os.environ.get("OIDC_USERS_LOGIN_VALIDITY_DURATION", 60 * 60)
    )  # seconds

    OIDC_AUTHENTICATE_CLASS = "users.views.authentication.OIDCAuthenticationRequestView"
    OIDC_CALLBACK_CLASS = "users.views.authentication.OIDCAuthenticationCallbackView"

    OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
    OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO")

    OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT")
    OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT")
    OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT")
    OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_URI")

    OIDC["OP"]["URL"] = os.environ.get("OIDC_OP_URL").removesuffix("/")
    OIDC["OP"]["DISPLAY_NAME"] = os.environ.get("OIDC_OP_DISPLAY_NAME", OIDC["OP"]["URL"])

    OIDC["OP"]["SUPPORTS_REFRESH"] = False
    OIDC["USERS"]["USE_REFRESH_TOKEN"] = to_bool(os.environ.get("OIDC_USERS_USE_REFRESH_TOKEN", "false"))

    op_settings = None
    try:
        op_settings = requests.get(OIDC["OP"]["URL"] + "/.well-known/openid-configuration").json()
    except Exception as e:
        _LOGGER.error(f"Could not fetch OIDC info from provider: {e}")

    if op_settings:
        if not OIDC_OP_AUTHORIZATION_ENDPOINT:
            OIDC_OP_AUTHORIZATION_ENDPOINT = op_settings.get("authorization_endpoint")
        if not OIDC_OP_TOKEN_ENDPOINT:
            OIDC_OP_TOKEN_ENDPOINT = op_settings.get("token_endpoint")
        if not OIDC_OP_USER_ENDPOINT:
            OIDC_OP_USER_ENDPOINT = op_settings.get("userinfo_endpoint")
        if not OIDC_OP_JWKS_ENDPOINT:
            OIDC_OP_JWKS_ENDPOINT = op_settings.get("jwks_uri")

    if not all([OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_USER_ENDPOINT]):
        raise Exception("Invalid configuration")

    if OIDC["USERS"]["USE_REFRESH_TOKEN"]:
        if "offline_access" in op_settings.get("scopes_supported", []):
            OIDC["OP"]["SUPPORTS_REFRESH"] = True
            OIDC_RP_SCOPES = "openid email offline_access"
            OIDC_AUTH_REQUEST_EXTRA_PARAMS = {"prompt": "consent"}
        elif "google.com" in OIDC["OP"]["URL"] and "refresh_token" in op_settings.get("grant_types_supported", []):
            # that's right, Google uses some nonstandard mechanism
            OIDC["OP"]["SUPPORTS_REFRESH"] = True
            OIDC_AUTH_REQUEST_EXTRA_PARAMS = {"access_type": "offline", "prompt": "consent"}

        if not OIDC["OP"]["SUPPORTS_REFRESH"]:
            _LOGGER.error(
                "Could not enable background OIDC refresh,"
                " falling back to periodic foreground refreshes"
                f" every {OIDC['USERS_LOGIN_VALIDITY_DURATION']} seconds"
            )
