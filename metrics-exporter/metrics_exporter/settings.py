import os


def str_to_bool(str_value: str) -> bool:
    """converts a string value to a boolean

    Args:
        str_value (str): string to convert to a boolean

    Returns:
        bool: a boolean corresponding to the input string value
    """
    return str_value.lower() in ["true", "yes", "1"]


# This is copied from the backend settings
def build_broker_url(user: str, pasword: str, host: str, port: str) -> str:
    """Builds a redis connection string

    Args:
        user (str): redis user
        pasword (str): redis password
        host (str): redis hostname
        port (str): redis port

    Returns:
        str: a connection string of the form "redis://user:password@hostname:port//"
    """
    conn_info = ""
    conn_port = ""
    if user and pasword:
        conn_info = f"{user}:{pasword}@"
    if port:
        conn_port = f":{port}"
    return f"redis://{conn_info}{host}{conn_port}//"


# App settings
PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/")  # nosec
PORT = int(os.environ.get("PORT", 8001))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Celery settings
CELERY_MONITORING_ENABLED = str_to_bool(os.environ.get("CELERY_MONITORING_ENABLED", "False"))
# For convenience we use the same settings as in the backend
CELERY_BROKER_USER = os.environ.get("CELERY_BROKER_USER", "redis")
CELERY_BROKER_PASSWORD = os.environ.get("CELERY_BROKER_PASSWORD", "redis")
CELERY_BROKER_HOST = os.environ.get("CELERY_BROKER_HOST", "localhost")
CELERY_BROKER_PORT = os.environ.get("CELERY_BROKER_PORT", "5672")
CELERY_BROKER_URL = build_broker_url(CELERY_BROKER_USER, CELERY_BROKER_PASSWORD, CELERY_BROKER_HOST, CELERY_BROKER_PORT)
