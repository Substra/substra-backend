# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerAggregateTuple


@shared_task
def createLedgerAggregateTupleAsync(args):
    return createLedgerAggregateTuple(args)
