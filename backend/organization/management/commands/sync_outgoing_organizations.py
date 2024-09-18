from django.db import models

from organization.models import OutgoingOrganization

from .base_sync import BaseSyncCommand
from .base_sync import Element


class Command(BaseSyncCommand):
    help = "Sync outgoing organizations"
    model = OutgoingOrganization
    model_name = "Outgoing organization"
    field_key = "organization_id"

    # Password saved as clear text
    def update_password(self, element: Element) -> models.Model:
        model = self.get(element.key)
        model.secret = element.password
        model.save()
        self.stdout.write(f"{self.model_name} updated: {element.key}")
        return model

    def create(self, element: Element) -> models.Model:
        model = self.model.objects.create(
            organization_id=element.key,
            secret=element.password,
        )
        self.stdout.write(f"{self.model_name} created: {element.key}")
        return model
