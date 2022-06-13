from django.core.management.base import BaseCommand

from organization.models import OutgoingOrganization


def pretty(s1, s2):
    return f"{s1.ljust(64)} | {s2.ljust(128)}"


class Command(BaseCommand):
    help = "Get outgoing organizations"

    def add_arguments(self, parser):
        parser.add_argument("organization_id", nargs="?")

    def handle(self, *args, **options):
        self.stdout.write(pretty("organization_id", "secret"))
        self.stdout.write(pretty("_" * 64, "_" * 128))

        if options["organization_id"]:
            try:
                outgoing_organization = OutgoingOrganization.objects.get(organization_id=options["organization_id"])
            except OutgoingOrganization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Organization with id {options["organization_id"]} does not exist'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(pretty(outgoing_organization.organization_id, outgoing_organization.secret))
                )
        else:
            outgoing_organizations = OutgoingOrganization.objects.all()
            for organization in outgoing_organizations:
                self.stdout.write(self.style.SUCCESS(pretty(organization.organization_id, organization.secret)))
