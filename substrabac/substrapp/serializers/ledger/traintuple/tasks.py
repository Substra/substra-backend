# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerTraintuple


@shared_task
def createLedgerTraintupleAsync(args):
    return createLedgerTraintuple(args)
