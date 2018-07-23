# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from substrapp.conf import conf
from substrapp.utils import invokeLedger


@shared_task
def createLedgerTraintuple(args):
    # TODO put in settings
    org = conf['orgs']['chu-nantes']
    peer = org['peers'][0]

    options = {
        'org': org,
        'peer': peer,
        'args': '{"Args":["createTraintuple", ' + args + ']}'
    }
    data, st = invokeLedger(options)

    return data, st
