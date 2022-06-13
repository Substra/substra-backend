from django.core.management.base import BaseCommand

from organization.models import IncomingOrganization
from organization.models import Organization


class Command(BaseCommand):
    help = "Create a new incoming organization"

    def add_arguments(self, parser):
        parser.add_argument("organization_id")
        parser.add_argument("secret", nargs="?", default=Organization.generate_secret())

    def handle(self, *args, **options):
        if IncomingOrganization.objects.filter(organization_id=options["organization_id"]).exists():
            self.stdout.write(self.style.NOTICE(f'organization with id {options["organization_id"]} already exists'))
        else:
            incoming_organization = IncomingOrganization.objects.create(
                organization_id=options["organization_id"],
                secret=options["secret"],
            )

            self.stdout.write(self.style.SUCCESS("organization successfully created"))
            self.stdout.write(f"organization_id={incoming_organization.organization_id}")
            self.stdout.write(f"secret={incoming_organization.secret}")
