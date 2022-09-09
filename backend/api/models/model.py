from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.model_pb2 as model_pb2
from api.models.utils import AssetPermissionMixin
from api.models.utils import URLValidatorWithOptionalTLD


class Model(models.Model, AssetPermissionMixin):
    """Model represent an output model and its associated metadata"""

    class Category(models.TextChoices):
        MODEL_SIMPLE = model_pb2.ModelCategory.Name(model_pb2.MODEL_SIMPLE)
        MODEL_HEAD = model_pb2.ModelCategory.Name(model_pb2.MODEL_HEAD)

    key = models.UUIDField(primary_key=True)
    category = models.CharField(max_length=64, choices=Category.choices)
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
