import os

# App settings
PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/")
PORT = int(os.environ.get("PORT", 8001))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
