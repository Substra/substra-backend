# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerObjective


@shared_task
def createLedgerObjectiveAsync(args, pkhash):
    return createLedgerObjective(args, pkhash)
