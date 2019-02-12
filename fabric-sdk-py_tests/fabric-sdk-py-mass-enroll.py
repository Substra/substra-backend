import random
import string

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
    print('Admin successfully enrolled')
    with open('/substra/data/orgs/owkin/ca-cert.pem', 'rb') as f:
        cert = f.read()

    if cacli._ca_client.get_cainfo() == cert:
        print('Distant ca cert is the same as in local filesystem')

    for x in range(0, 200):
        username = ''.join(
            [random.choice(string.ascii_letters + string.digits) for n in
             range(9)])
        print(f'Will try to register user {username}')
        try:
            secret = admin.register(username, role='client', affiliation='owkin.nantes')
        except ValueError as e:
            print(e)
        else:
            print(f'Correctly registered user {username} with secret {secret}')
