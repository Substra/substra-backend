import random
import string
from pprint import pprint

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

    print('Create identity Service')

    identityService = cacli.newIdentityService()

    username = ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in
         range(9)])
    print(f'Will try to register user {username}')
    secret = identityService.create(admin, username)
    print(f'Correctly registered user {username} with secret {secret}')

    print(f'Will try to get user {username}')
    res = identityService.getOne(username, admin)
    pprint(res)
    print('Will try to get all users')
    res = identityService.getAll(admin)
    print('number of users: ', len(res['result']['identities']))

    print(f'Will try to update user {username} with maxEnrollments=3, affiliation=\'.\' and secret=bar')
    res = identityService.update(username, admin, maxEnrollments=3,
                                 affiliation='.', enrollmentSecret='bar')
    pprint(res)

    print(f'Will try to enroll user {username} with original password {secret}')
    try:
        cacli.enroll(username, secret)
    except:
        print('User cannot enroll with old password')
    else:
        print('/!\ User password update did not work correctly as he is able to enroll with old password')
    finally:
        print(f'Will try to enroll user {username} with modified password bar')
        cacli.enroll(username, 'bar')

        print(f'Will try to get user {username} to see changes')
        res = identityService.getOne(username, admin)
        pprint(res)

        print(f'Will try to delete user {username}')
        res = identityService.delete(username, admin)
        pprint(res)

        print(f'Will try to get deleted user {username}')
        res = identityService.getOne(username, admin)
        pprint(res)
