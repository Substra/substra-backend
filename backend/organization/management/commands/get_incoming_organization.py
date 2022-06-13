from django.core.management.base import BaseCommand

from organization.models import IncomingOrganization


def pretty(s1, s2):
    return f"{s1.ljust(64)} | {s2.ljust(128)}"


class Command(BaseCommand):
    help = "Get incoming organizations"

    def add_arguments(self, parser):
        parser.add_argument("organization_id", nargs="?")

    def handle(self, *args, **options):
        self.stdout.write(pretty("organization_id", "secret"))
        self.stdout.write(pretty("_" * 64, "_" * 128))

        if options["organization_id"]:
            try:
                incoming_organization = IncomingOrganization.objects.get(organization_id=options["organization_id"])
            except IncomingOrganization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Organization with id {options["organization_id"]} does not exist'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(pretty(incoming_organization.organization_id, incoming_organization.secret))
                )
        else:
            incoming_organizations = IncomingOrganization.objects.all()
            for organization in incoming_organizations:
                self.stdout.write(self.style.SUCCESS(pretty(organization.organization_id, organization.secret)))
