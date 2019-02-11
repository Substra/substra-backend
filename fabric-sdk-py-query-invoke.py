import json
import os
import random
import string
from pprint import pprint

from hfc.fabric_ca.caservice import ca_service

from hfc.fabric import Client

cli = Client(net_profile="./network_new.json")
admin_owkin = cli.get_user('owkin', 'admin')

cli.new_channel('mychannel')

from hfc.fabric_ca.caservice import ca_service

cacli = ca_service(target="https://rca-owkin:7054",
                   ca_certs_path='/substra/data/orgs/owkin/ca-cert.pem',
                   ca_name='rca-owkin')

print('Will try to enroll admin')
try:
    admin = cacli.enroll('admin-owkin', 'admin-owkinpw')
except ValueError as e:
    print(e)
else:

    response = cli.chaincode_query(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin'],
        args=[],
        cc_name='mycc',
        cc_version='1.0',
        fcn='queryChallenges'
    )
    print(response)

    response = cli.query_installed_chaincodes(
        requestor=admin_owkin,
        peer_names=['peer1-owkin']
    )
    print(response)

    response = cli.query_channels(
        requestor=admin_owkin,
        peer_names=['peer1-owkin']
    )
    print(response)

    response = cli.query_info(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin']
    )
    print(response)

    dir_path = os.path.dirname(os.path.realpath(__file__))

    response = cli.chaincode_invoke(
        requestor=admin_owkin,
        channel_name='mychannel',
        peer_names=['peer1-owkin'],
        args=['ISIC 2018',
              'ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994',
              'http://chunantes.substrabac:8001/media/datasets/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/opener.py',
              'Images',
              'ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994',
              'http://chunantes.substrabac:8001/media/datasets/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/description.md',
              '',
              'all'
              ],
        cc_name='mycc',
        cc_version='1.0',
        fcn='registerDataset'
    )
    print(response)
