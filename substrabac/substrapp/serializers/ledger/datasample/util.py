from __future__ import absolute_import, unicode_literals

from substrapp.models import DataSample
from substrapp.ledger_utils import invoke_ledger
from substrapp.serializers.ledger.utils import create_ledger_assets


def createLedgerDataSample(args, pkhashes, sync=False):
    return create_ledger_assets(
        model=DataSample,
        fcn='registerDataSample',
        args=args,
        pkhashes=pkhashes,
        sync=sync)


def updateLedgerDataSample(args, sync=False):
    args = {
        'hashes': args[0],
        'dataManagerKeys': args[1],
    }
    return invoke_ledger(fcn='updateDataSample', args=args, sync=sync)
