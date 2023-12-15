from .mods.oidc import *
from .test import *

DEBUG = True

# Enable Browsable API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += ("rest_framework.renderers.BrowsableAPIRenderer",)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
    "libs.session_authentication.CustomSessionAuthentication",
]

# Allow locally deployed frontend
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
ALLOWED_HOSTS = ALLOWED_HOSTS + ["127.0.0.1", ".org-1.com"]
COMMON_HOST_DOMAIN = "org-1.com"

MSP_ID = os.environ.get("MSP_ID", "MyOrg1MSP")

CHANNELS["mychannel"]["model_export_enabled"] = False
