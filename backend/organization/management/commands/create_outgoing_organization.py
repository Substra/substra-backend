from django.core.management.base import BaseCommand

from organization.models import Organization
from organization.models import OutgoingOrganization


class Command(BaseCommand):
    help = "Create a new outgoing organization"

    def add_arguments(self, parser):
        parser.add_argument("organization_id")
        parser.add_argument("secret", nargs="?", default=Organization.generate_password())

    def handle(self, *args, **options):
        if OutgoingOrganization.objects.filter(organization_id=options["organization_id"]).exists():
            self.stdout.write(self.style.NOTICE(f'organization with id {options["organization_id"]} already exists'))
        else:
            outgoing_organization = OutgoingOrganization.objects.create(
                organization_id=options["organization_id"],
                secret=options["secret"],
            )

            self.stdout.write(self.style.SUCCESS("outgoing organization successfully created"))
            self.stdout.write(f"organization_id={outgoing_organization.organization_id}")
