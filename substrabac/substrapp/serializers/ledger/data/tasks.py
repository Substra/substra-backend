# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerData


@shared_task
def createLedgerDataAsync(args, pkhash):
    return createLedgerData(args, pkhash)
