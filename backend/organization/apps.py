from django.apps import AppConfig
from django.db.models.signals import pre_save


class OrganizationConfig(AppConfig):
    name = "organization"

    def ready(self):
        from organization.models import IncomingOrganization
        from organization.signals.organization.pre_save import organization_pre_save

        pre_save.connect(organization_pre_save, sender=IncomingOrganization)
