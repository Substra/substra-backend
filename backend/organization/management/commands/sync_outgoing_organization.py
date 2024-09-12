from organization.models import OutgoingOrganization

from .base_sync_organization import BaseSyncOrganizationCommand


class Command(BaseSyncOrganizationCommand):
    help = "Sync outgoing organizations"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = OutgoingOrganization
        self.model_name = "Outgoing organization"

    def update_password(self, key: str, password: str) -> None:
        element = self.model.objects.get(organization_id=key)
        element.secret = password
        element.save()
        self.stdout.write(f"{self.model_name} updated: {key}")

    def create(self, key: str, password: str) -> None:
        self.model.objects.create(
            organization_id=key,
            secret=password,
        )
        self.stdout.write(f"{self.model_name} created: {key}")
