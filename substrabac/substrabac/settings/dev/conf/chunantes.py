# using chu-nantes org
from os import path

from substrabac.settings.common import PROJECT_ROOT
from substrapp.conf import conf

org = conf['orgs']['chu-nantes']
peer = org['peers'][0]

# get owner which is the worker of the trainData
signcert = path.join(PROJECT_ROOT, 'substrapp/conf/chu-nantes/user/msp/signcerts/cert.pem')
