from django.conf import settings

from orchestrator.client import OrchestratorClient


def get_orchestrator_client(channel_name: str = None) -> OrchestratorClient:
    host = f"{settings.ORCHESTRATOR_HOST}:{settings.ORCHESTRATOR_PORT}"

    cacert = None
    client_key = None
    client_cert = None

    if settings.ORCHESTRATOR_TLS_ENABLED:
        cacert = settings.ORCHESTRATOR_TLS_SERVER_CACERT_PATH

    if settings.ORCHESTRATOR_MTLS_ENABLED:
        client_key = settings.ORCHESTRATOR_TLS_CLIENT_KEY_PATH
        client_cert = settings.ORCHESTRATOR_TLS_CLIENT_CERT_PATH

    mspid = settings.MSP_ID

    opts = (
        ("grpc.keepalive_time_ms", settings.ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS),
        ("grpc.keepalive_timeout_ms", settings.ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS),
        ("grpc.keepalive_permit_without_calls", settings.ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS),
        ("grpc.http2.max_pings_without_data", settings.ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA),
    )

    return OrchestratorClient(host, channel_name, mspid, cacert, client_key, client_cert, opts=opts)
