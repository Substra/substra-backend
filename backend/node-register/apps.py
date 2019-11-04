import time
import logging
from django.apps import AppConfig
from django.conf import settings
from substrapp.ledger_utils import invoke_ledger

from aiogrpc import RpcError

logger = logging.getLogger(__name__)


class NodeRegisterConfig(AppConfig):
    name = 'node-register'

    def ready(self):

        # We try until success if dev mode, if it fails the backend will not start
        # In production we let this app fails
        while True:
            try:
                # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
                invoke_ledger(fcn='registerNode', args=[''], sync=True)
            except RpcError as e:
                if not settings.DEBUG:
                    raise
                logger.exception(e)
                time.sleep(5)
                logger.info('Retry to register the node to the ledger')
            else:
                logger.info('Node registered in the ledger')
                return
