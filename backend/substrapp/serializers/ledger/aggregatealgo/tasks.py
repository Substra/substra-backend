# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerAggregateAlgo


@shared_task
def createLedgerAggregateAlgoAsync(args, pkhash):
    return createLedgerAggregateAlgo(args, pkhash)
