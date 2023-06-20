"""
SECRET_KEY is built in Django, but also used for signing JWTs
"""

import os
import pathlib
import secrets

from . import path
from .utils import to_bool

SECRET_KEY_PATH = os.environ.get("SECRET_KEY_PATH", os.path.normpath(os.path.join(path.PROJECT_ROOT, "SECRET")))


def _generate_secret_key():
    return secrets.token_urlsafe()  # uses a "reasonable default" length


_SECRET_KEY_LOAD_AND_STORE = to_bool(
    os.environ.get("SECRET_KEY_LOAD_AND_STORE", "True")
)  # Whether to load the secret key from file (and write it there if it doesn't exist)

if _SECRET_KEY_LOAD_AND_STORE:
    try:
        SECRET_KEY = pathlib.Path(SECRET_KEY_PATH).read_text().strip()
    except IOError:
        try:
            SECRET_KEY = _generate_secret_key()
            with open(SECRET_KEY_PATH, "w") as fp:
                fp.write(SECRET_KEY)
        except IOError:
            raise Exception(f"Cannot open file `{SECRET_KEY_PATH}` for writing.")
else:
    SECRET_KEY = _generate_secret_key()
