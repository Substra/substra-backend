from organization.models import IncomingOrganization

from .base_sync_organization import BaseSyncOrganizationCommand


class Command(BaseSyncOrganizationCommand):
    help = "Sync incoming organizations"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = IncomingOrganization
        self.model_name = "Incoming organization"
