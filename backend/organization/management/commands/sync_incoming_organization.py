from organization.models import IncomingOrganization

from .base_sync import BaseSyncCommand


class Command(BaseSyncCommand):
    help = "Sync incoming organizations"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = IncomingOrganization
        self.model_name = "Incoming organization"
        self.field_key = "organization_id"
