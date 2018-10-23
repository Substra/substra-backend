# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerAlgo


@shared_task
def createLedgerAlgoAsync(args, pkhash):
    return createLedgerAlgo(args, pkhash)
