# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerAggregate


@shared_task
def createLedgerAggregateAsync(args):
    return createLedgerAggregate(args)
