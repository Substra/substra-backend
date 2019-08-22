from django.core.management.base import BaseCommand, CommandError
from node.models import Node, IncomingNode


class Command(BaseCommand):
    help = 'Create a new incoming node'

    def add_arguments(self, parser):
        parser.add_argument('node_id')

    def handle(self, *args, **options):
        incoming_node, created = IncomingNode.objects.get_or_create(node_id=options['node_id'], secret=Node.generate_secret())

        if not created:
            self.stdout.write(self.style.NOTICE(f'node with id {incoming_node.node_id} already exists'))
        else:
            self.stdout.write(self.style.SUCCESS('node successfully created'))
            self.stdout.write(f'node_id={incoming_node.node_id}')
            self.stdout.write(f'secret={incoming_node.secret}')
