import time
import logging
from django.apps import AppConfig
from django.conf import settings
from substrapp.ledger_utils import invoke_ledger

from aiogrpc import RpcError

logger = logging.getLogger(__name__)
LEDGER = getattr(settings, 'LEDGER', None)


class NodeRegisterConfig(AppConfig):
    name = 'node-register'

    def register_node(self, channel):
        # We try until success, if it fails the backend will not start
        while True:
            try:
                # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
                invoke_ledger(channel, fcn='registerNode', args=[''], sync=True)
            except RpcError as e:
                if not settings.DEBUG:
                    raise
                logger.exception(e)
                time.sleep(5)
                logger.info(f'({channel}) Retry to register the node to the ledger')
            else:
                logger.error(f'({channel}) Node registered in the ledger')
                return

    def ready(self):
        for channel in LEDGER['channels']:
            self.register_node(channel)
