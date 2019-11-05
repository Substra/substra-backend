# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerTesttuple


@shared_task
def createLedgerTesttupleAsync(args):
    return createLedgerTesttuple(args)
