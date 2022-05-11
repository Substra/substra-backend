import structlog
from django.db import models
from django.db.models import Count
from django.db.models import Q

import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
from localrep.models.computetask import CATEGORY_CHOICES
from localrep.models.computetask import ComputeTask
from localrep.models.utils import get_enum_choices

logger = structlog.get_logger(__name__)


class ComputePlan(models.Model):
    """ComputePlan represent a compute plan and its associated metadata"""

    STATUS_CHOICES = get_enum_choices(computeplan_pb2.ComputePlanStatus)

    key = models.UUIDField(primary_key=True)
    owner = models.CharField(max_length=100)
    delete_intermediary_models = models.BooleanField(null=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=computeplan_pb2.ComputePlanStatus.PLAN_STATUS_UNKNOWN)
    tag = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    metadata = models.JSONField(null=True)
    failed_task_key = models.CharField(max_length=100, null=True)
    failed_task_category = models.IntegerField(choices=CATEGORY_CHOICES, null=True)
    channel = models.CharField(max_length=100)

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations

    def _add_failed_task(self) -> None:
        if self.failed_task_key is not None:
            # failed_task field is already populated
            return

        first_failed_task = (
            self.compute_tasks.filter(end_date__isnull=False, status=computetask_pb2.ComputeTaskStatus.STATUS_FAILED)
            .order_by("end_date")
            .first()
        )

        if first_failed_task is None:
            return

        self.failed_task_key = first_failed_task.key
        self.failed_task_category = first_failed_task.category

    def update_status(self) -> None:
        """
        Compute cp status from tasks counts.
        See: `orchestrator/lib/persistence/computeplan_dbal.go`
        """
        stats = ComputeTask.objects.filter(compute_plan__key=str(self.key)).aggregate(
            task_count=Count("key"),
            done_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DONE)),
            waiting_count=Count("key", filter=Q(status=computetask_pb2.STATUS_WAITING)),
            todo_count=Count("key", filter=Q(status=computetask_pb2.STATUS_TODO)),
            doing_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DOING)),
            canceled_count=Count("key", filter=Q(status=computetask_pb2.STATUS_CANCELED)),
            failed_count=Count("key", filter=Q(status=computetask_pb2.STATUS_FAILED)),
        )

        if stats["task_count"] == 0:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_UNKNOWN
        elif stats["done_count"] == stats["task_count"]:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_DONE
        elif stats["failed_count"] > 0:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_FAILED
        elif stats["canceled_count"] > 0:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_CANCELED
        elif stats["waiting_count"] == stats["task_count"]:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_WAITING
        elif stats["waiting_count"] < stats["task_count"] and stats["doing_count"] == 0 and stats["done_count"] == 0:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_TODO
        else:
            compute_plan_status = computeplan_pb2.PLAN_STATUS_DOING

        logger.debug(
            "update cp status",
            status=compute_plan_status,
            task_count=stats["task_count"],
            done_count=stats["task_count"],
            waiting_count=stats["waiting_count"],
            todo_count=stats["todo_count"],
            doing_count=stats["done_count"],
            canceled_count=stats["canceled_count"],
            failed_count=stats["doing_count"],
        )

        self.status = compute_plan_status

        if self.status == computeplan_pb2.PLAN_STATUS_FAILED:
            self._add_failed_task()

        self.save()

    def update_dates(self) -> None:
        """Update start_date, end_date"""

        if not self.start_date:
            first_started_task = self.compute_tasks.filter(start_date__isnull=False).order_by("start_date").first()
            if first_started_task:
                self.start_date = first_started_task.start_date

        ongoing_tasks = self.compute_tasks.filter(end_date__isnull=True).exists()
        failed_or_canceled_tasks = self.compute_tasks.filter(
            status__in=(
                computeplan_pb2.PLAN_STATUS_FAILED,
                computeplan_pb2.PLAN_STATUS_CANCELED,
            )
        ).exists()
        # some tasks could remain in waiting status without end date
        if ongoing_tasks and not failed_or_canceled_tasks:
            self.end_date = None  # end date could be reset when cp is updated with new tasks
        else:
            last_ended_task = self.compute_tasks.filter(end_date__isnull=False).order_by("end_date").last()
            if last_ended_task:
                self.end_date = last_ended_task.end_date

        self.save()
