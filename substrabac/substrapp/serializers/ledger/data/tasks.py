# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerData, updateLedgerData


@shared_task
def createLedgerDataAsync(args, pkhashes):
    return createLedgerData(args, pkhashes)

@shared_task
def updateLedgerDataAsync(args, pkhashes):
    return updateLedgerData(args, pkhashes)\
