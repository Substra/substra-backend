from django.db import models


class ComputePlan(models.Model):
    """ComputePlan represent a compute plan and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    owner = models.CharField(max_length=100)
    delete_intermediary_models = models.BooleanField(null=True)
    tag = models.CharField(max_length=100, blank=True)
    creation_date = models.DateTimeField()
    metadata = models.JSONField(null=True)
    channel = models.CharField(max_length=100)
