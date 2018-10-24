# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerDataset


@shared_task
def createLedgerDatasetAsync(args, pkhash):
    return createLedgerDataset(args, pkhash)
