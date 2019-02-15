from pprint import pprint

from hfc.fabric_ca.caservice import ca_service

cacli = ca_service(target="https://rca-owkin:7054",
                   ca_certs_path='/substra/data/orgs/owkin/ca-cert.pem',
                   ca_name='rca-owkin')

print('Will try to enroll bootstrap admin')
try:
    bootstrap_admin = cacli.enroll('admin', 'adminpw')
except ValueError as e:
    print(e)
else:
    print('Admin successfully enrolled')

    print('Create affiliation Service')

    affiliationService = cacli.newAffiliationService()

    affiliation = 'department3'

    print(f'Will try to create affiliation {affiliation}')
    res = affiliationService.create(bootstrap_admin, affiliation)
    pprint(res)

    print(f'Will try to get affiliation {affiliation}')
    res = affiliationService.getOne(affiliation, bootstrap_admin)
    pprint(res)

    print('Will try to get all affiliations')
    res = affiliationService.getAll(bootstrap_admin)
    print('number of affiliations: ', len(res['result']['affiliations']))

    print(f'Will try to update affiliation {affiliation} with name=\'department3bis\'')
    res = affiliationService.update(affiliation, bootstrap_admin, name='department3bis')
    pprint(res)

    print(f'Will try to get affiliation {affiliation} to see changes')
    res = affiliationService.getOne(affiliation, bootstrap_admin)
    pprint(res)

    print(f'Will try to delete affiliation {affiliation}')
    res = affiliationService.delete('department3bis', bootstrap_admin)
    pprint(res)

    print(f'Will try to get deleted affiliation {affiliation}')
    res = affiliationService.getOne(affiliation, bootstrap_admin)
    pprint(res)
