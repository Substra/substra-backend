from django.contrib.postgres.fields import ArrayField
from django.db import models

from localrep.models.utils import URLValidatorWithOptionalTLD


class Metric(models.Model):
    """Metric represent a metric and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    description_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    description_checksum = models.CharField(max_length=64)
    metric_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    metric_checksum = models.CharField(max_length=64)
    permissions_download_public = models.BooleanField()
    permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    permissions_process_public = models.BooleanField()
    permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    metadata = models.JSONField()
    channel = models.CharField(max_length=100)

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
