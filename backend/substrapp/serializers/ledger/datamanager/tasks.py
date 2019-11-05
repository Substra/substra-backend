# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerDataManager, updateLedgerDataManager


@shared_task
def createLedgerDataManagerAsync(args, pkhash):
    return createLedgerDataManager(args, pkhash)


@shared_task
def updateLedgerDataManagerAsync(args):
    return updateLedgerDataManager(args)
