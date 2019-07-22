# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerComputePlan


@shared_task
def createLedgerComputePlanAsync(args):
    return createLedgerComputePlan(args)
