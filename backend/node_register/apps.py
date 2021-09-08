import time
import logging
import multiprocessing
from grpc import StatusCode
from django.apps import AppConfig
from django.conf import settings
from substrapp.orchestrator.api import get_orchestrator_client
from substrapp.orchestrator.error import OrcError

logger = logging.getLogger(__name__)


def _register_node(channel_name):
    # We try until success, if it fails the backend will not start
    while True:
        with get_orchestrator_client(channel_name) as client:
            try:
                client.register_node()
            except OrcError as rpc_error:
                code = rpc_error.code
                if code == StatusCode.ALREADY_EXISTS:
                    break
                time.sleep(1)
                logger.exception(rpc_error)
                logger.info(f'({channel_name}) Retry registring the node on the orchestrator')
            else:
                logger.info(f'({channel_name}) Node registered on the orchestrator')
                break


class NodeRegisterConfig(AppConfig):
    name = 'node_register'

    def register_node(self, channel_name):
        proc = multiprocessing.Process(target=_register_node, args=[channel_name])
        proc.start()

    def ready(self):
        for channel_name in settings.LEDGER_CHANNELS.keys():
            self.register_node(channel_name)
