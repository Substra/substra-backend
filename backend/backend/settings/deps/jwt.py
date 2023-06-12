import os
import pathlib
import secrets

from .. import common

# SECURITY WARNING: keep the secret key used in production secret!
JWT_SECRET_PATH = os.environ.get("JWT_SECRET_PATH", os.path.normpath(os.path.join(common.PROJECT_ROOT, "SECRET")))

# Key configuration for JSON web tokens (JWT) authentication
if common.to_bool(os.environ.get("JWT_SECRET_NEEDED", "False")):
    try:
        SECRET_KEY = pathlib.Path(JWT_SECRET_PATH).read_text().strip()
    except IOError:
        try:
            SECRET_KEY = secrets.token_urlsafe()  # uses a "reasonable default" length
            with open(JWT_SECRET_PATH, "w") as fp:
                fp.write(SECRET_KEY)
        except IOError:
            raise Exception(f"Cannot open file `{JWT_SECRET_PATH}` for writing.")
else:
    SECRET_KEY = "unused default value " + secrets.token_urlsafe()
