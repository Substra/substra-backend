from django.apps import AppConfig
from substrapp.ledger_utils import invoke_ledger


class NodeConfig(AppConfig):
    name = 'node'

    def ready(self):
        # args is set to empty because fabric-sdk-py doesn't allow None args for invoke operations
        invoke_ledger(fcn='registerNode', args=[''], sync=True)
