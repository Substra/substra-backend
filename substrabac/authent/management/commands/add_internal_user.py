from django.conf import settings
from django.core.management import BaseCommand

from authent.models import Permission, InternalAuthent
from substrabac.settings.deps.ledger import get_csr, get_hashed_modulus


class Command(BaseCommand):
    help = '''
    Add internal user for checking its permission
    '''

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('permission', type=str)

    def handle(self, *args, **options):

        LEDGER = getattr(settings, 'LEDGER', None)

        # load args
        username = options['username']
        pwd = options['password']
        permission_name = options['permission']

        pkey = LEDGER['hfc_ca']['pkey']
        cacli = LEDGER['hfc_ca']['client']

        # get or create permission if does not exist
        p, _ = Permission.objects.get_or_create(name=permission_name)

        csr = get_csr(pkey, username)
        enrollment = cacli.enroll(username, pwd, csr=csr)

        hashed_modulus = get_hashed_modulus(enrollment.cert)
        # get or create internal authent
        i, _ = InternalAuthent.objects.get_or_create(permission=p, modulus=hashed_modulus)
