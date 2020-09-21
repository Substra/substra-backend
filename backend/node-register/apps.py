import time
import logging
from django.apps import AppConfig
from django.conf import settings
from substrapp.ledger_utils import invoke_ledger

logger = logging.getLogger(__name__)
LEDGER = getattr(settings, 'LEDGER', None)


class NodeRegisterConfig(AppConfig):
    name = 'node-register'

    def register_node(self, channel_name):
        # We try until success, if it fails the backend will not start
        while True:
            try:
                # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
                invoke_ledger(channel_name, fcn='registerNode', args=[''], sync=True)
            except Exception as e:
                logger.exception(e)
                time.sleep(1)
                logger.info(f'({channel_name}) Retry registring the node on the ledger')
            else:
                logger.info(f'({channel_name}) Node registered on the ledger')
                return

    def ready(self):
        for channel_name in LEDGER['channels']:
            self.register_node(channel_name)
