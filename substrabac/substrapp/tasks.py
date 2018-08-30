from __future__ import absolute_import, unicode_literals
from substrabac.celery import app
from substrapp.conf import conf
from substrapp.utils import queryLedger


@app.task
def queryTraintuples():
    # using chu-nantes as in our testing owkin has been revoked
    org = conf['orgs']['chu-nantes']
    peer = org['peers'][0]

    owner = '6f194a5a7a54ba295dc5a6c185d1a1404e2bc9b2d2be7aa097c2d47c01429ccc'
    data, st = queryLedger({
        'org': org,
        'peer': peer,
        'args': '{"Args":["queryFilter","traintuple~trainWorker~status","%s, todo"]}' % owner
    })

    if st == 200:
        todos = [x for x in data if x['status'] == 'todo']

        for model in todos:
            traintuple = ''
            # Log Start TrainTest
            data, st = queryLedger({
                'org': org,
                'peer': peer,
                'args': '{"Args":["logStartTrainTest","%s","training"]}' % traintuple
            })
