import uuid

from django.db import models
from django.db.models import Q


class ComputePlanWorkerMapping(models.Model):
    """A mapping between a compute plan and a celery worker"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    compute_plan_key = models.UUIDField()
    worker_index = models.IntegerField()
    release_date = models.DateTimeField(null=True, default=None)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["compute_plan_key"],
                condition=Q(release_date=None),
                name="unique_empty_release_date_for_each_compute_plan",
            ),
        ]
