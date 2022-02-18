from django.db import models

from localrep.models.computetask import CATEGORY_CHOICES


class ComputePlan(models.Model):
    """ComputePlan represent a compute plan and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    owner = models.CharField(max_length=100)
    delete_intermediary_models = models.BooleanField(null=True)
    tag = models.CharField(max_length=100, blank=True)
    creation_date = models.DateTimeField()
    metadata = models.JSONField(null=True)
    failed_task_key = models.CharField(max_length=100, null=True)
    failed_task_category = models.IntegerField(choices=CATEGORY_CHOICES, null=True)
    channel = models.CharField(max_length=100)
