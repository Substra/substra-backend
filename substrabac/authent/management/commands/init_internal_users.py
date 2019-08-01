import json
import os

from django.conf import settings
from django.core.management import BaseCommand

from substrabac.settings.deps.ledger import get_csr, get_hashed_modulus
from authent.models import Permission, InternalAuthent


class Command(BaseCommand):
    help = '''
    Init internal users
    '''

    def handle(self, *args, **options):

        LEDGER = getattr(settings, 'LEDGER', None)

        pkey = LEDGER['hfc_ca']['pkey']
        cacli = LEDGER['hfc_ca']['client']

        # create mapping of known cert
        # external_path = LEDGER['external']['path']
        SUBSTRA_PATH = os.environ.get('SUBSTRA_PATH', '/substra')
        ORG = os.environ.get('SUBSTRABAC_ORG', 'substra')
        USERS_FILE = os.environ.get('USERS_FILE', f'{SUBSTRA_PATH}/conf/{ORG}/substrabac/users-list.json')
        with open(USERS_FILE, 'r+') as f:
            data = json.load(f)

            for permission_name in data.keys():

                # get or create permission if does not exist
                p, _ = Permission.objects.get_or_create(name=permission_name)

                # enroll user to get cert
                for username in data[p.name].keys():
                    pwd = data[p.name][username]

                    csr = get_csr(pkey, username)
                    try:
                        enrollment = cacli.enroll(username, pwd, csr=csr)
                    except:
                        pass
                    else:
                        hashed_modulus = get_hashed_modulus(enrollment.cert)
                        # get or create internal authent
                        i, _ = InternalAuthent.objects.get_or_create(permission=p, modulus=hashed_modulus)
