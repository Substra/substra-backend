from django.apps import AppConfig
from substrapp.ledger_utils import invoke_ledger

from django.conf import settings


class NodeRegisterConfig(AppConfig):
    name = 'node-register'

    def ready(self):
        if hasattr(settings, 'LEDGER'):
            # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
            invoke_ledger(fcn='registerNode', args=[''], sync=True)
