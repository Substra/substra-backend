from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.algo_pb2 as algo_pb2
from localrep.models.utils import URLValidatorWithOptionalTLD
from localrep.models.utils import get_enum_choices


class Algo(models.Model):
    """Algo represent an algorithm and its associated metadata"""

    CATEGORY_CHOICES = get_enum_choices(algo_pb2.AlgoCategory)

    key = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
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
