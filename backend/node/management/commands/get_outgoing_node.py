from django.core.management.base import BaseCommand

from node.models import OutgoingNode


def pretty(s1, s2):
    return f"{s1.ljust(64)} | {s2.ljust(128)}"


class Command(BaseCommand):
    help = "Get outgoing nodes"

    def add_arguments(self, parser):
        parser.add_argument("node_id", nargs="?")

    def handle(self, *args, **options):
        self.stdout.write(pretty("node_id", "secret"))
        self.stdout.write(pretty("_" * 64, "_" * 128))

        if options["node_id"]:
            try:
                outgoing_node = OutgoingNode.objects.get(node_id=options["node_id"])
            except OutgoingNode.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Node with id {options["node_id"]} does not exist'))
            else:
                self.stdout.write(self.style.SUCCESS(pretty(outgoing_node.node_id, outgoing_node.secret)))
        else:
            outgoing_nodes = OutgoingNode.objects.all()
            for node in outgoing_nodes:
                self.stdout.write(self.style.SUCCESS(pretty(node.node_id, node.secret)))
