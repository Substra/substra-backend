from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.common_pb2 as common_pb2
from api.models.utils import AssetPermissionMixin
from api.models.utils import URLValidatorWithOptionalTLD
from orchestrator import function_pb2


class FunctionInput(models.Model):
    class Kind(models.TextChoices):
        ASSET_DATA_SAMPLE = common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_SAMPLE)
        ASSET_DATA_MANAGER = common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_MANAGER)
        ASSET_MODEL = common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL)

    function = models.ForeignKey("Function", on_delete=models.deletion.CASCADE, related_name="inputs")
    identifier = models.CharField(max_length=100)
    kind = models.CharField(max_length=64, choices=Kind.choices)
    optional = models.BooleanField(default=False)
    multiple = models.BooleanField(default=False)
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("function", "identifier"),)
        ordering = ["identifier"]  # default order for relations serializations


class FunctionOutput(models.Model):
    class Kind(models.TextChoices):
        ASSET_MODEL = common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL)
        ASSET_PERFORMANCE = common_pb2.AssetKind.Name(common_pb2.ASSET_PERFORMANCE)

    function = models.ForeignKey("Function", on_delete=models.deletion.CASCADE, related_name="outputs")
    identifier = models.CharField(max_length=100)
    kind = models.CharField(max_length=64, choices=Kind.choices)
    multiple = models.BooleanField(default=False)
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("function", "identifier"),)
        ordering = ["identifier"]  # default order for relations serializations


class Function(models.Model, AssetPermissionMixin):
    """Function represent a function and its associated metadata"""

    Status = models.TextChoices(
        "Status", [(status_name, status_name) for status_name in function_pb2.FunctionStatus.keys()]
    )

    key = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    description_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    description_checksum = models.CharField(max_length=64)
    archive_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    archive_checksum = models.CharField(max_length=64)
    image_address = models.URLField(validators=[URLValidatorWithOptionalTLD()], null=True)
    image_checksum = models.CharField(max_length=64, null=True)
    permissions_download_public = models.BooleanField()
    permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    permissions_process_public = models.BooleanField()
    permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    metadata = models.JSONField()
    channel = models.CharField(max_length=100)
    status = models.CharField(max_length=64, choices=Status.choices)

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
