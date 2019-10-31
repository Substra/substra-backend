# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerCompositeTraintuple


@shared_task
def createLedgerCompositeTraintupleAsync(args):
    return createLedgerCompositeTraintuple(args)
