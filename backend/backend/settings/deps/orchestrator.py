import os

from .. import common

ORCHESTRATOR_HOST = os.environ.get("ORCHESTRATOR_HOST")
ORCHESTRATOR_PORT = os.environ.get("ORCHESTRATOR_PORT")
ORCHESTRATOR_TLS_ENABLED = common.to_bool(os.environ.get("ORCHESTRATOR_TLS_ENABLED"))
ORCHESTRATOR_MTLS_ENABLED = common.to_bool(os.environ.get("ORCHESTRATOR_MTLS_ENABLED"))
ORCHESTRATOR_TLS_SERVER_CACERT_PATH = os.environ.get("ORCHESTRATOR_TLS_SERVER_CACERT_PATH")
ORCHESTRATOR_TLS_CLIENT_CERT_PATH = os.environ.get("ORCHESTRATOR_TLS_CLIENT_CERT_PATH")
ORCHESTRATOR_TLS_CLIENT_KEY_PATH = os.environ.get("ORCHESTRATOR_TLS_CLIENT_KEY_PATH")
ORCHESTRATOR_RETRY_DELAY = 1
ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS = int(os.environ.get("ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS", "10000"))
