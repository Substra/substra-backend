from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.models.utils import AssetPermissionMixin
from api.models.utils import URLValidatorWithOptionalTLD


class DataManager(models.Model, AssetPermissionMixin):
    """Datamanager represent a datamanager and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    description_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    description_checksum = models.CharField(max_length=64)
    opener_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    opener_checksum = models.CharField(max_length=64)
    permissions_download_public = models.BooleanField()
    permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    permissions_process_public = models.BooleanField()
    permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    logs_permission_public = models.BooleanField()
    logs_permission_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    type = models.CharField(max_length=100)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    metadata = models.JSONField()
    channel = models.CharField(max_length=100)

    def get_data_samples(self):
        # the join operation generates duplicates
        return self.data_samples.distinct()

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
