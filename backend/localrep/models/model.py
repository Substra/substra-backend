from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.model_pb2 as model_pb2
from localrep.models.utils import AssetPermissionMixin
from localrep.models.utils import URLValidatorWithOptionalTLD
from localrep.models.utils import get_enum_choices

CATEGORY_CHOICES = get_enum_choices(model_pb2.ModelCategory)


class Model(models.Model, AssetPermissionMixin):
    """Model represent an output model and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    compute_task = models.ForeignKey("ComputeTask", on_delete=models.deletion.DO_NOTHING, related_name="models")
    model_address = models.URLField(validators=[URLValidatorWithOptionalTLD()], null=True)  # disabled model
    model_checksum = models.CharField(max_length=64)
    permissions_download_public = models.BooleanField()
    permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    permissions_process_public = models.BooleanField()
    permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
