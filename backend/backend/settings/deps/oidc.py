import logging
import os

import requests

from .. import common
from . import ledger

_LOGGER = logging.getLogger(__name__)

OIDC_ENABLED = common.to_bool(os.environ.get("OIDC_ENABLED", "false"))
if OIDC_ENABLED:  # noqa: C901
    common.INSTALLED_APPS += ["mozilla_django_oidc"]  # load after auth
    common.AUTHENTICATION_BACKENDS += ["users.authentication.SubstraOIDCAuthenticationBackend"]
    common.LOGGING["loggers"]["mozilla_django_oidc"] = {
        "level": common.LOG_LEVEL,
        "handlers": ["console"],
        "propagate": False,
    }

    if common.to_bool(os.environ.get("OIDC_USERS_APPEND_DOMAIN", "false")):
        OIDC_USERNAME_ALGO = "users.utils.username_with_domain_from_email"
    else:
        OIDC_USERNAME_ALGO = "users.utils.username_from_email"

    OIDC_USERS_DEFAULT_CHANNEL = os.environ.get("OIDC_USERS_DEFAULT_CHANNEL")
    if not OIDC_USERS_DEFAULT_CHANNEL:
        raise Exception("No default channel provided for OIDC users")
    if OIDC_USERS_DEFAULT_CHANNEL not in ledger.LEDGER_CHANNELS:
        raise Exception(f"Channel {OIDC_USERS_DEFAULT_CHANNEL} does not exist")

    OIDC_AUTHENTICATE_CLASS = "users.views.authentication.SubstraOIDCAuthenticationRequestView"
    OIDC_CALLBACK_CLASS = "users.views.authentication.SubstraOIDCAuthenticationCallbackView"

    OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
    OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO")

    OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT")
    OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT")
    OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT")
    OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_URI")

    _OIDC_OP_URL = os.environ.get("OIDC_OP_URL").removesuffix("/")
    OIDC_OP_DISPLAY_NAME = os.environ.get("OIDC_OP_DISPLAY_NAME")
    if not OIDC_OP_DISPLAY_NAME:
        OIDC_OP_DISPLAY_NAME = _OIDC_OP_URL

    # put the OP URL before the endpoints, but not JWKS
    # (it is specified as URI, not endpoint, despite the mozilla_django_oidc name)
    for endpoint in ["OIDC_OP_AUTHORIZATION_ENDPOINT", "OIDC_OP_TOKEN_ENDPOINT", "OIDC_OP_USER_ENDPOINT"]:
        if globals()[endpoint]:
            globals()[endpoint] = _OIDC_OP_URL + globals()[endpoint]

    if not all([OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_USER_ENDPOINT, OIDC_OP_JWKS_ENDPOINT]):
        try:
            op_settings = requests.get(_OIDC_OP_URL + "/.well-known/openid-configuration").json()
            if not OIDC_OP_AUTHORIZATION_ENDPOINT:
                OIDC_OP_AUTHORIZATION_ENDPOINT = op_settings.get("authorization_endpoint")
            if not OIDC_OP_TOKEN_ENDPOINT:
                OIDC_OP_TOKEN_ENDPOINT = op_settings.get("token_endpoint")
            if not OIDC_OP_USER_ENDPOINT:
                OIDC_OP_USER_ENDPOINT = op_settings.get("userinfo_endpoint")
            if not OIDC_OP_JWKS_ENDPOINT:
                OIDC_OP_JWKS_ENDPOINT = op_settings.get("jwks_uri")
        except Exception as e:
            _LOGGER.error(f"Could not fetch OIDC info from provider: {e}")
