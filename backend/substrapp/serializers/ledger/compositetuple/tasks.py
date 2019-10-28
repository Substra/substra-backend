# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerCompositetuple


@shared_task
def createLedgerCompositetupleAsync(args):
    return createLedgerCompositetuple(args)
