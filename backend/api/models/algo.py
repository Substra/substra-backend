from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
from api.models.utils import AssetPermissionMixin
from api.models.utils import URLValidatorWithOptionalTLD


class AlgoInput(models.Model):
    class Kind(models.TextChoices):
        ASSET_DATA_SAMPLE = common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_SAMPLE)
        ASSET_DATA_MANAGER = common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_MANAGER)
        ASSET_MODEL = common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL)

    algo = models.ForeignKey("Algo", on_delete=models.deletion.CASCADE, related_name="inputs")
    identifier = models.CharField(max_length=100)
    kind = models.CharField(max_length=64, choices=Kind.choices)
    optional = models.BooleanField(default=False)
    multiple = models.BooleanField(default=False)

    class Meta:
        unique_together = (("algo", "identifier"),)
        ordering = ["identifier"]  # default order for relations serializations


class AlgoOutput(models.Model):
    class Kind(models.TextChoices):
        ASSET_MODEL = common_pb2.AssetKind.Name(common_pb2.ASSET_MODEL)
        ASSET_PERFORMANCE = common_pb2.AssetKind.Name(common_pb2.ASSET_PERFORMANCE)

    algo = models.ForeignKey("Algo", on_delete=models.deletion.CASCADE, related_name="outputs")
    identifier = models.CharField(max_length=100)
    kind = models.CharField(max_length=64, choices=Kind.choices)
    multiple = models.BooleanField(default=False)

    class Meta:
        unique_together = (("algo", "identifier"),)
        ordering = ["identifier"]  # default order for relations serializations


class Algo(models.Model, AssetPermissionMixin):
    """Algo represent an algorithm and its associated metadata"""

    class Category(models.TextChoices):
        ALGO_SIMPLE = algo_pb2.AlgoCategory.Name(algo_pb2.ALGO_SIMPLE)
        ALGO_AGGREGATE = algo_pb2.AlgoCategory.Name(algo_pb2.ALGO_AGGREGATE)
        ALGO_COMPOSITE = algo_pb2.AlgoCategory.Name(algo_pb2.ALGO_COMPOSITE)
        ALGO_METRIC = algo_pb2.AlgoCategory.Name(algo_pb2.ALGO_METRIC)
        ALGO_PREDICT = algo_pb2.AlgoCategory.Name(algo_pb2.ALGO_PREDICT)

    key = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=64, choices=Category.choices)
    description_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    description_checksum = models.CharField(max_length=64)
    algorithm_address = models.URLField(validators=[URLValidatorWithOptionalTLD()])
    algorithm_checksum = models.CharField(max_length=64)
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
