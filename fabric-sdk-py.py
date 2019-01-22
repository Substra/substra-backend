from hfc.fabric_ca.caservice import ca_service
from hfc.fabric import Client

cli = Client(net_profile="./network.json")
admin_owkin = cli.get_user('owkin', 'admin')


response = cli.chaincode_invoke(
               requestor=admin_owkin,
               channel_name='mychannel',
               peer_names=['peer1-owkin'],
               args=['queryAll'],
               cc_name='mycc',
               cc_version='v1.0'
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


cacli = ca_service(target="https://rca-owkin:7054", ca_certs_path='/substra/data/orgs/owkin/ca-cert.pem', ca_name='rca-owkin')

print('Will try to enroll admin')
try:
    admin = cacli.enroll('admin-owkin', 'admin-owkinpw')
except ValueError as e:
    print(e)
else:
    print('Admin successfully enrolled')
    with open('/substra/data/orgs/owkin/ca-cert.pem', 'rb') as f:
        cert = f.read()

    if cacli._ca_client.get_cainfo() == cert:
        print('Distant ca cert is the same as in local filesystem')






    # user = 'user12'
    # print(f'Will try to register user {user}')
    # try:
    #     secret = admin.register(user)
    # except ValueError as e:
    #     print(e)
    # else:
    #     print(f'Correctly registered user {user} with secret {secret}')
    #     print(f'Will try to enroll new registered user {user} with secret {secret}')
    #
    #     try:
    #         User = cli.enroll(user, secret)
    #     except ValueError as e:
    #         print(e)
    #     else:
    #         print(f'User {user} successfully enrolled')
