from django.core.management.base import BaseCommand

from node.models import IncomingNode
from node.models import Node


class Command(BaseCommand):
    help = "Create a new incoming node"

    def add_arguments(self, parser):
        parser.add_argument("node_id")
        parser.add_argument("secret", nargs="?", default=Node.generate_secret())

    def handle(self, *args, **options):
        if IncomingNode.objects.filter(node_id=options["node_id"]).exists():
            self.stdout.write(self.style.NOTICE(f'node with id {options["node_id"]} already exists'))
        else:
            incoming_node = IncomingNode.objects.create(
                node_id=options["node_id"],
                secret=options["secret"],
            )

            self.stdout.write(self.style.SUCCESS("node successfully created"))
            self.stdout.write(f"node_id={incoming_node.node_id}")
            self.stdout.write(f"secret={incoming_node.secret}")
