# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerCompositeAlgo


@shared_task
def createLedgerCompositeAlgoAsync(args, pkhash):
    return createLedgerCompositeAlgo(args, pkhash)
