import os

from ..deps.ledger import *
from ..deps.orchestrator import *
from ..dev import *

ORCHESTRATOR_RABBITMQ_ACTIVTY_TIMEOUT = int(os.getenv("ORCHESTRATOR_RABBITMQ_ACTIVTY_TIMEOUT", 1800))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_celery_results",
    "rest_framework",
    "localrep",
    "events",
    "substrapp",
    "users",
]
