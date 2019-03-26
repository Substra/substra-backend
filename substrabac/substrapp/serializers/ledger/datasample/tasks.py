# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerDataSample, updateLedgerDataSample


@shared_task
def createLedgerDataSampleAsync(args, pkhashes):
    return createLedgerDataSample(args, pkhashes)

@shared_task
def updateLedgerDataSampleAsync(args):
    return updateLedgerDataSample(args)
