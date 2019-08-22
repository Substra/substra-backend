from django.core.management.base import BaseCommand, CommandError
from node.models import Node, OutgoingNode


class Command(BaseCommand):
    help = 'Create a new outgoing node'

    def add_arguments(self, parser):
        parser.add_argument('node_id')

    def handle(self, *args, **options):
        outgoing_node, created = OutgoingNode.objects.get_or_create(node_id=options['node_id'], secret=Node.generate_secret())

        if not created:
            self.stdout.write(self.style.NOTICE(f'node with id {outgoing_node.node_id} already exists'))
        else:
            self.stdout.write(self.style.SUCCESS('node successfully created'))
            self.stdout.write(f'node_id={outgoing_node.node_id}')
            self.stdout.write(f'secret={outgoing_node.secret}')
