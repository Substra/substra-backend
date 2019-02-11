import random
import string

from hfc.fabric_ca.caservice import ca_service

cacli = ca_service(target="https://rca-owkin:7054",
                   ca_certs_path='/substra/data/orgs/owkin/ca-cert.pem',
                   ca_name='rca-owkin')

print('Will try to enroll admin')
try:
    bootstrap_admin = cacli.enroll('admin', 'adminpw')
except ValueError as e:
    print(e)
else:
    print('Admin successfully enrolled')

    print('Create affiliation Service')

    certificateService = cacli.newCertificateService()

    print(f'Will try to get certificates')
    res = certificateService.getCertificates(bootstrap_admin)
    print(len(res['result']))

    print(f'Will try to get certificates admin')
    res = certificateService.getCertificates(bootstrap_admin, 'admin')
    print(len(res['result']))

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

        print(f'Will try to get certificates {username} from admin')
        res = certificateService.getCertificates(admin, username)
        print(len(res['result']))

        print(
            f'Will try to enroll user {username} with original password {secret}')
        try:
            user = cacli.enroll(username, secret)
        except:
            print('User cannot enroll with old password')
        else:

            print(f'Will try to get certificates {username} from user')
            res = certificateService.getCertificates(user)
            print(res)
