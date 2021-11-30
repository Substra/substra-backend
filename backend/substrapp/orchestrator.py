from django.conf import settings

from orchestrator.client import OrchestratorClient


def get_orchestrator_client(channel_name):

    host = f"{settings.ORCHESTRATOR_HOST}:{settings.ORCHESTRATOR_PORT}"

    cacert = None
    client_key = None
    client_cert = None

    if settings.ORCHESTRATOR_TLS_ENABLED:
        cacert = settings.ORCHESTRATOR_TLS_SERVER_CACERT_PATH

    if settings.ORCHESTRATOR_MTLS_ENABLED:
        client_key = settings.ORCHESTRATOR_TLS_CLIENT_KEY_PATH
        client_cert = settings.ORCHESTRATOR_TLS_CLIENT_CERT_PATH

    mspid = settings.LEDGER_MSP_ID
    chaincode = settings.LEDGER_CHANNELS[channel_name]["chaincode"]["name"]

    return OrchestratorClient(host, channel_name, mspid, chaincode, cacert, client_key, client_cert, opts=None)
