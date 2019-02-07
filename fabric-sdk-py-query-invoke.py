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
                   args=['queryChallenges'],
                   cc_name='mycc',
                   cc_version='1.0'
                   )
    print(response)
    #
    # response = cli.query_installed_chaincodes(
    #                requestor=admin_owkin,
    #                peer_names=['peer1-owkin']
    #                )
    # print(response)
    #
    # response = cli.query_channels(
    #                requestor=admin_owkin,
    #                peer_names=['peer1-owkin']
    #                )
    # print(response)
    #
    # response = cli.query_info(
    #                requestor=admin_owkin,
    #                channel_name='mychannel',
    #                peer_names=['peer1-owkin']
    #                )
    # print(response)



