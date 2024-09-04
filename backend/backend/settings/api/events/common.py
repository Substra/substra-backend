from ...deps.ledger import *
from ...deps.orchestrator import *
from ...dev import *

# order is important for api and substrapp because of overriding commands
# https://docs.djangoproject.com/en/4.1/howto/custom-management-commands/#overriding-commands

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "api",
    "substrapp",
    "users",
    "organization",
]
