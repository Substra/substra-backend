"""
JSON web tokens
"""

import os
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_LIFETIME", 24 * 60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("REFRESH_TOKEN_LIFETIME", 24 * 60 * 7))),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("JWT",),
    "BLACKLIST_AFTER_ROTATION": True,
}

# To encode unique jwt token generated with reset password request
RESET_JWT_SIGNATURE_ALGORITHM = "HS256"
