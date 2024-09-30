from organization.models import IncomingOrganization

from .base_sync import BaseSyncCommand


class Command(BaseSyncCommand):
    help = "Sync incoming organizations"
    model = IncomingOrganization
    model_name = "Incoming organization"
    field_key = "organization_id"
