import time
import logging
import multiprocessing
from django.apps import AppConfig
from django.conf import settings
from substrapp.ledger.api import invoke_ledger

logger = logging.getLogger(__name__)


def _register_node(channel_name):
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
            break


class NodeRegisterConfig(AppConfig):
    name = 'node-register'

    def register_node(self, channel_name):
        proc = multiprocessing.Process(target=_register_node, args=[channel_name])
        proc.start()

    def ready(self):
        for channel_name in settings.LEDGER_CHANNELS.keys():
            self.register_node(channel_name)
