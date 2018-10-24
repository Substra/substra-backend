# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .util import createLedgerChallenge


@shared_task
def createLedgerChallengeAsync(args, pkhash):
    return createLedgerChallenge(args, pkhash)
