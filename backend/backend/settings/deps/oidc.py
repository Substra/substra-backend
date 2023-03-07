import logging
import os

import requests

_LOGGER = logging.getLogger(__name__)


from .. import common

OIDC_ENABLED = common.to_bool(os.environ.get("OIDC_ENABLED", "false"))
if OIDC_ENABLED:
    common.INSTALLED_APPS += ["mozilla_django_oidc"]  # load after auth
    common.AUTHENTICATION_BACKENDS += ["mozilla_django_oidc.auth.OIDCAuthenticationBackend"]
    common.LOGGING["loggers"]["mozilla_django_oidc"] = {
        "level": common.LOG_LEVEL,
        "handlers": ["console"],
        "propagate": False,
    }

    if common.to_bool(os.environ.get("OIDC_USERS_SUFFIX_DOMAIN", "false")):
        OIDC_USERNAME_ALGO = "users.utils.username_with_domain_from_email"
    else:
        OIDC_USERNAME_ALGO = "users.utils.username_from_email"

    OIDC_CALLBACK_CLASS = "users.views.authentication.OIDCAuthenticationCallbackJwtView"

    OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
    OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO")

    OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT")
    OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT")
    OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT")
    OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_URI")

    _OIDC_OP_URL = os.environ.get("OIDC_OP_URL").removesuffix("/")

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
