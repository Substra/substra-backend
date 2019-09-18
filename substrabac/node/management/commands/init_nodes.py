import json

from django.core.management.base import BaseCommand
from node.models import IncomingNode, OutgoingNode


class Command(BaseCommand):
    help = 'Load nodes from file'

    def add_arguments(self, parser):
        parser.add_argument('file')

    def handle(self, *args, **options):

        filepath = options['file']

        print(filepath)
        with open(filepath) as json_file:
            data = json.load(json_file)

            for node in data['incoming_nodes']:
                IncomingNode.objects.create(node_id=node['node_id'], secret=node['secret'])
                self.stdout.write(self.style.SUCCESS('created incoming node'))
            for node in data['outgoing_nodes']:
                OutgoingNode.objects.create(node_id=node['node_id'], secret=node['secret'])
                self.stdout.write(self.style.SUCCESS('created outgoing node'))
