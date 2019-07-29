from django.conf import settings
from django.core.management import BaseCommand

from authent.models import Node, ExternalAuthent
from substrabac.settings.deps.ledger import get_csr, get_hashed_modulus


class Command(BaseCommand):
    help = '''
    Add user to external node for sending its credentials
    '''

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('node', type=str)

    def handle(self, *args, **options):

        LEDGER = getattr(settings, 'LEDGER', None)

        # load args
        username = options['username']
        pwd = options['password']
        node_name = options['node']

        pkey = LEDGER['hfc_ca']['pkey']
        cacli = LEDGER['hfc_ca']['client']

        # get or create permission if does not exist
        n, _ = Node.objects.get_or_create(name=node_name)

        csr = get_csr(pkey, username)
        enrollment = cacli.enroll(username, pwd, csr=csr)

        hashed_modulus = get_hashed_modulus(enrollment.cert)
        # get or create internal authent
        e, _ = ExternalAuthent.objects.get_or_create(node=n, modulus=hashed_modulus)

