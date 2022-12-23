from django.contrib.postgres.fields import ArrayField
from django.db import models

import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
from api.models.algo import AlgoInput
from api.models.algo import AlgoOutput
from api.models.datasample import DataSample
from api.models.utils import AssetPermissionMixin
from api.models.utils import URLValidatorWithOptionalTLD


class ComputeTaskInput(models.Model):
    task = models.ForeignKey("ComputeTask", on_delete=models.CASCADE, related_name="inputs")
    identifier = models.CharField(max_length=100)
    position = models.IntegerField()
    # either asset_key or (parent task, output identifier) is specified by the user
    asset_key = models.UUIDField(null=True, blank=True)
    parent_task_key = models.ForeignKey("ComputeTask", on_delete=models.SET_NULL, null=True, blank=True)
    parent_task_output_identifier = models.CharField(max_length=100, null=True, blank=True)
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("task", "identifier", "position"),)
        ordering = ["position"]


class ComputeTaskOutput(models.Model):
    task = models.ForeignKey("ComputeTask", on_delete=models.CASCADE, related_name="outputs")
    identifier = models.CharField(max_length=100)
    permissions_download_public = models.BooleanField()
    permissions_download_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    permissions_process_public = models.BooleanField()
    permissions_process_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    transient = models.BooleanField(default=False)
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("task", "identifier"),)


class ComputeTaskInputAsset(models.Model):
    task_input = models.OneToOneField("ComputeTaskInput", on_delete=models.CASCADE, related_name="asset")
    asset_kind = models.CharField(max_length=64, choices=AlgoInput.Kind.choices)
    asset_key = models.UUIDField()
    channel = models.CharField(max_length=100)


class ComputeTaskOutputAsset(models.Model):
    task_output = models.ForeignKey("ComputeTaskOutput", on_delete=models.CASCADE, related_name="assets")
    asset_kind = models.CharField(max_length=64, choices=AlgoOutput.Kind.choices)
    asset_key = models.CharField(max_length=73)  # performance have composite key: key1|key2
    channel = models.CharField(max_length=100)


class ComputeTask(models.Model, AssetPermissionMixin):
    """ComputeTask represent a computetask and its associated metadata"""

    class Category(models.TextChoices):
        TASK_UNKNOWN = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_UNKNOWN)
        TASK_TRAIN = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN)
        TASK_AGGREGATE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_AGGREGATE)
        TASK_COMPOSITE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_COMPOSITE)
        TASK_PREDICT = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_PREDICT)
        TASK_TEST = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TEST)

    class Status(models.TextChoices):
        STATUS_WAITING = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_WAITING)
        STATUS_TODO = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_TODO)
        STATUS_DOING = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_DOING)
        STATUS_DONE = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_DONE)
        STATUS_CANCELED = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_CANCELED)
        STATUS_FAILED = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_FAILED)

    class ErrorType(models.TextChoices):
        ERROR_TYPE_BUILD = failure_report_pb2.ErrorType.Name(failure_report_pb2.ERROR_TYPE_BUILD)
        ERROR_TYPE_EXECUTION = failure_report_pb2.ErrorType.Name(failure_report_pb2.ERROR_TYPE_EXECUTION)
        ERROR_TYPE_INTERNAL = failure_report_pb2.ErrorType.Name(failure_report_pb2.ERROR_TYPE_INTERNAL)

    key = models.UUIDField(primary_key=True)
    category = models.CharField(max_length=64, choices=Category.choices, default=Category.TASK_UNKNOWN)
    algo = models.ForeignKey("Algo", on_delete=models.CASCADE, related_name="compute_tasks")
    owner = models.CharField(max_length=100)
    compute_plan = models.ForeignKey("ComputePlan", on_delete=models.deletion.CASCADE, related_name="compute_tasks")
    rank = models.IntegerField()
    status = models.CharField(max_length=64, choices=Status.choices)
    worker = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    error_type = models.CharField(max_length=64, choices=ErrorType.choices, null=True)
    tag = models.CharField(max_length=100, null=True, blank=True)
    logs_permission_public = models.BooleanField()
    logs_permission_authorized_ids = ArrayField(models.CharField(max_length=1024), size=100)
    logs_address = models.URLField(validators=[URLValidatorWithOptionalTLD()], null=True)
    logs_checksum = models.CharField(max_length=64, null=True)
    logs_owner = models.CharField(max_length=100, null=True)
    channel = models.CharField(max_length=100)
    metadata = models.JSONField()

    # specific fields for train, composite and test tasks
    # patch waiting for a solution to preserve related datasample order without sync time overhead
    data_manager = models.ForeignKey(
        "DataManager", null=True, on_delete=models.deletion.CASCADE, related_name="compute_tasks"
    )
    data_samples = models.ManyToManyField(DataSample, through="TaskDataSamples", related_name="compute_tasks")

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations

    # used for logs download
    def is_public(self, _):
        return self.logs_permission_public

    def get_authorized_ids(self, _):
        return self.logs_permission_authorized_ids

    def get_owner(self):
        return self.logs_owner


class TaskDataSamples(models.Model):
    """preserve datasamples order in this relation"""

    compute_task = models.ForeignKey(ComputeTask, on_delete=models.CASCADE, related_name="compute_task_data_sample")
    data_sample = models.ForeignKey(DataSample, on_delete=models.CASCADE, related_name="data_sample_task")
    order = models.IntegerField(default=0)
