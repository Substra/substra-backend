"""
Task broker settings
"""

import os

from substrapp.compute_tasks.errors import CeleryRetryError

from .org import ORG_NAME


def build_broker_url(user: str, password: str, host: str, port: str) -> str:
    """Builds a redis connection string

    Args:
        user (str): redis user
        password (str): redis password
        host (str): redis hostname
        port (str): redis port

    Returns:
        str: a connection string of the form "redis://user:password@hostname:port//"
    """
    conn_info = ""
    conn_port = ""
    if user and password:
        conn_info = f"{user}:{password}@"
    if port:
        conn_port = f":{port}"
    return f"redis://{conn_info}{host}{conn_port}//"


CELERY_BROKER_USER = os.environ.get("CELERY_BROKER_USER")
CELERY_BROKER_PASSWORD = os.environ.get("CELERY_BROKER_PASSWORD")
CELERY_BROKER_HOST = os.environ.get("CELERY_BROKER_HOST", "localhost")
CELERY_BROKER_PORT = os.environ.get("CELERY_BROKER_PORT", "5672")
CELERY_BROKER_URL = build_broker_url(CELERY_BROKER_USER, CELERY_BROKER_PASSWORD, CELERY_BROKER_HOST, CELERY_BROKER_PORT)

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_TRACK_STARTED = True  # since 4.0

# With these settings, tasks will be retried for up to a maximum of 127 minutes.
#
# max_wait = CELERY_TASK_RETRY_BACKOFF * sum(2 ** n for n in range(CELERY_TASK_MAX_RETRIES))
#          = 60 * (1 + 2 + 4 + 8 + 16 + 32 + 64)
#          = 127 minutes
#
# Since jitter is enabled, the actual cumulative wait can be much less than max_wait. From the doc
# (https://docs.celeryproject.org/en/stable/userguide/tasks.html#Task.retry_jitter):
#
# > If this option is set to True, the delay value calculated by retry_backoff is treated as a maximum, and the actual
# > delay value will be a random number between zero and that maximum.
CELERY_TASK_AUTORETRY_FOR = (CeleryRetryError,)
CELERY_TASK_MAX_RETRIES = int(os.environ.get("CELERY_TASK_MAX_RETRIES", 7))
CELERY_TASK_RETRY_BACKOFF = int(os.environ.get("CELERY_TASK_RETRY_BACKOFF", 60))  # time in seconds
CELERY_TASK_RETRY_BACKOFF_MAX = int(os.environ.get("CELERY_TASK_RETRY_BACKOFF_MAX", 64 * 60))
CELERY_TASK_RETRY_JITTER = True

CELERY_WORKER_CONCURRENCY = int(os.environ.get("CELERY_WORKER_CONCURRENCY", 1))
CELERY_BROADCAST = f"{ORG_NAME}.broadcast"

CELERYBEAT_FLUSH_EXPIRED_TOKENS_TASK_PERIOD = os.environ.get("CELERYBEAT_FLUSH_EXPIRED_TOKENS_TASK_PERIOD", 24 * 3600)
