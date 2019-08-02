from django.core.management import BaseCommand

from authent.models import Node, ExternalAuthent


class Command(BaseCommand):
    help = '''
    Add user to external node for sending its credentials
    '''

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('node', type=str)

    def handle(self, *args, **options):
        # load args
        username = options['username']
        pwd = options['password']
        node_name = options['node']

        # get or create permission if does not exist
        n, _ = Node.objects.get_or_create(name=node_name)

        # get or create external authent
        e, _ = ExternalAuthent.objects.get_or_create(node=n, username=username, password=pwd)
