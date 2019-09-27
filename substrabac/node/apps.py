from django.apps import AppConfig
from substrapp.ledger_utils import invoke_ledger

from django.conf import settings


class NodeConfig(AppConfig):
    name = 'node'

    def ready(self):
        if hasattr(settings, 'REGISTER_NODE') and getattr(settings, 'REGISTER_NODE'):
            # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
            invoke_ledger(fcn='registerNode', args=[''], sync=True)
