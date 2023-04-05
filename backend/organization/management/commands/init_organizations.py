import json

from django.core.management.base import BaseCommand

from organization.models import IncomingOrganization
from organization.models import OutgoingOrganization


class Command(BaseCommand):
    help = "Load organizations from file"

    def add_arguments(self, parser):
        parser.add_argument("file")

    def handle(self, *args, **options):
        filepath = options["file"]

        with open(filepath) as json_file:
            data = json.load(json_file)

            for organization in data["incoming_organizations"]:
                IncomingOrganization.objects.create(
                    organization_id=organization["organization_id"], password=organization["password"]
                )
                self.stdout.write(self.style.SUCCESS("created incoming organization"))
            for organization in data["outgoing_organizations"]:
                OutgoingOrganization.objects.create(
                    organization_id=organization["organization_id"], secret=organization["secret"]
                )
                self.stdout.write(self.style.SUCCESS("created outgoing organization"))
