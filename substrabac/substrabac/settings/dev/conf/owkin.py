# using owkin org
from os import path

from substrabac.settings.common import PROJECT_ROOT
from substrapp.conf import conf

org = conf['orgs']['owkin']
peer = org['peers'][0]

# get owner which is the worker of the trainData
signcert = path.join(PROJECT_ROOT, 'substrapp/conf/owkin/user/msp/signcerts/cert.pem')
