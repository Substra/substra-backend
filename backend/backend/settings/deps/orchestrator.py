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

# @ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS: The period (in milliseconds) after which a keepalive ping is sent on the
# transport.
#
# NB: For keepalive to work properly and as intended, the client-side keepalive settings should be in agreement
# with the server-side settings. If a client sends pings more often than the server is willing to accept,
# the connection will be terminated with a GOAWAY frame with "too_many_pings" as the debug data.
ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS = int(common.must_get_env("ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS"))

# @ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS: The amount of time (in milliseconds) the sender of the keepalive ping
# waits for an acknowledgement. If it does not receive an acknowledgement within this time, it will close
# the connection.
ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS = int(common.must_get_env("ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS"))

# @ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS: If set to 1 (0: false; 1: true), allows keepalive pings
# to be sent even if there are no calls in flight.
ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS = bool(
    int(common.must_get_env("ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS"))
)

# @ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA The maximum number of pings that can be sent when there is
# no data/header frame to be sent. gRPC Core will not continue sending pings if we run over the limit.
# Setting it to 0 allows sending pings without such a restriction.
ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA = int(
    common.must_get_env("ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA")
)
