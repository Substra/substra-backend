from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from localrep.models.utils import get_enum_choices

CATEGORY_CHOICES = get_enum_choices(computetask_pb2.ComputeTaskCategory)
STATUS_CHOICES = get_enum_choices(computetask_pb2.ComputeTaskStatus)
ERROR_TYPE_CHOICES = get_enum_choices(failure_report_pb2.ErrorType)


class ComputeTask(models.Model):
    """ComputeTask represent a computetask and its associated metadata"""

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
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    error_type = models.IntegerField(choices=ERROR_TYPE_CHOICES, null=True)
    tag = models.CharField(max_length=100, null=True, blank=True)
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
