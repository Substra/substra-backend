import logging
import os

import requests

from .. import common
from . import ledger

_LOGGER = logging.getLogger(__name__)

# mozilla-django-oidc values are OIDC_*
# but to avoid polluting the global namespace
# we'll use an "OIDC" dict for any setting added by us

OIDC = {
    "ENABLED": common.to_bool(os.environ.get("OIDC_ENABLED", "false")),
    "USERS": {},
    "OP": {},
}
if OIDC["ENABLED"]:  # noqa: C901
    common.INSTALLED_APPS += ["mozilla_django_oidc"]  # load after auth
    common.AUTHENTICATION_BACKENDS += ["users.authentication.OIDCAuthenticationBackend"]
    common.LOGGING["loggers"]["mozilla_django_oidc"] = {
        "level": common.LOG_LEVEL,
        "handlers": ["console"],
        "propagate": False,
    }

    OIDC["USERS"]["APPEND_DOMAIN"] = common.to_bool(os.environ.get("OIDC_USERS_APPEND_DOMAIN", "false"))

    OIDC["USERS"]["DEFAULT_CHANNEL"] = os.environ.get("OIDC_USERS_DEFAULT_CHANNEL")
    if not OIDC["USERS"]["DEFAULT_CHANNEL"]:
        raise Exception("No default channel provided for OIDC users")
    if OIDC["USERS"]["DEFAULT_CHANNEL"] not in ledger.LEDGER_CHANNELS:
        raise Exception(f"Channel {OIDC['USERS']['DEFAULT_CHANNEL']} does not exist")
    OIDC["USERS"]["LOGIN_VALIDITY_DURATION"] = int(
        os.environ.get("OIDC_USERS_LOGIN_VALIDITY_DURATION", 60 * 60)  # seconds
    )

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
    OIDC["OP"]["DISPLAY_NAME"] = os.environ.get("OIDC_OP_DISPLAY_NAME")
    if not OIDC["OP"]["DISPLAY_NAME"]:
        OIDC["OP"]["DISPLAY_NAME"] = OIDC["OP"]["URL"]

    # put the OP URL before the endpoints, but not JWKS
    # (it is specified as URI, not endpoint, despite the mozilla_django_oidc name)
    for endpoint in ["OIDC_OP_AUTHORIZATION_ENDPOINT", "OIDC_OP_TOKEN_ENDPOINT", "OIDC_OP_USER_ENDPOINT"]:
        if globals()[endpoint]:
            globals()[endpoint] = OIDC["OP"]["URL"] + globals()[endpoint]

    OIDC["OP"]["SUPPORTS_REFRESH"] = False
    OIDC["USERS"]["USE_REFRESH_TOKEN"] = common.to_bool(os.environ.get("OIDC_USERS_USE_REFRESH_TOKEN", "false"))

    if (
        not all([OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_USER_ENDPOINT, OIDC_OP_JWKS_ENDPOINT])
        or OIDC["USERS"]["USE_REFRESH_TOKEN"]
    ):
        try:
            op_settings = requests.get(OIDC["OP"]["URL"] + "/.well-known/openid-configuration").json()
            if not OIDC_OP_AUTHORIZATION_ENDPOINT:
                OIDC_OP_AUTHORIZATION_ENDPOINT = op_settings.get("authorization_endpoint")
            if not OIDC_OP_TOKEN_ENDPOINT:
                OIDC_OP_TOKEN_ENDPOINT = op_settings.get("token_endpoint")
            if not OIDC_OP_USER_ENDPOINT:
                OIDC_OP_USER_ENDPOINT = op_settings.get("userinfo_endpoint")
            if not OIDC_OP_JWKS_ENDPOINT:
                OIDC_OP_JWKS_ENDPOINT = op_settings.get("jwks_uri")

            if OIDC["USERS"]["USE_REFRESH_TOKEN"] and "offline_access" in op_settings.get("scopes_supported", []):
                OIDC["OP"]["SUPPORTS_REFRESH"] = True
                OIDC_RP_SCOPES = "openid email offline_access"
                OIDC_AUTH_REQUEST_EXTRA_PARAMS = {"prompt": "consent"}
            elif (
                OIDC["USERS"]["USE_REFRESH_TOKEN"]
                and "google.com" in OIDC["OP"]["URL"]
                and "refresh_token" in op_settings.get("grant_types_supported", [])
            ):
                # that's right, Google uses some nonstandard mechanism
                OIDC["OP"]["SUPPORTS_REFRESH"] = True
                OIDC_AUTH_REQUEST_EXTRA_PARAMS = {"access_type": "offline", "prompt": "consent"}

            if OIDC["USERS"]["USE_REFRESH_TOKEN"] and not OIDC["OP"]["SUPPORTS_REFRESH"]:
                _LOGGER.error(
                    "Could not enable background OIDC refresh,"
                    " falling back to periodic foreground refreshes"
                    f" every {OIDC['USERS_LOGIN_VALIDITY_DURATION']} seconds"
                )

        except Exception as e:
            _LOGGER.error(f"Could not fetch OIDC info from provider: {e}")

        if not all([OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_USER_ENDPOINT]):
            raise Exception("Invalid configuration")
