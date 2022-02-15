from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.computetask_pb2 as computetask_pb2
from localrep.models.utils import get_enum_choices


class ComputeTask(models.Model):
    """ComputeTask represent a computetask and its associated metadata"""

    CATEGORY_CHOICES = get_enum_choices(computetask_pb2.ComputeTaskCategory)
    STATUS_CHOICES = get_enum_choices(computetask_pb2.ComputeTaskStatus)

    key = models.UUIDField(primary_key=True)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    algo = models.ForeignKey("Algo", on_delete=models.CASCADE, related_name="compute_tasks")
    owner = models.CharField(max_length=100)
    compute_plan = models.ForeignKey("ComputePlan", on_delete=models.deletion.CASCADE, related_name="compute_tasks")
    parent_tasks = ArrayField(models.CharField(max_length=1024), size=100, null=True)
    rank = models.IntegerField()
    status = models.IntegerField(choices=STATUS_CHOICES)
    worker = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    logs_permission_public = models.BooleanField()
    logs_permission_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    channel = models.CharField(max_length=100)
    metadata = models.JSONField()

    # specific fields for train, composite and test tasks
    data_manager = models.ForeignKey(
        "DataManager", null=True, on_delete=models.deletion.CASCADE, related_name="compute_tasks"
    )
    data_samples = models.ManyToManyField("DataSample", null=True, related_name="compute_tasks")

    # specific fields for train and aggregate tasks
    model_permissions_process_public = models.BooleanField(null=True)
    model_permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)
    model_permissions_download_public = models.BooleanField(null=True)
    model_permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)

    # specific fields for test tasks
    metrics = models.ManyToManyField("Metric", null=True, related_name="compute_tasks")

    # specific fields for composite tasks
    head_permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)
    head_permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)
    trunk_permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)
    trunk_permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100, null=True)
