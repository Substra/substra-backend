from django.db import models


class Performance(models.Model):
    compute_task_key = models.ForeignKey(
        "ComputeTask", on_delete=models.deletion.DO_NOTHING, related_name="performances"
    )
    metric_key = models.ForeignKey("Metric", on_delete=models.deletion.DO_NOTHING, related_name="performances")
    performance_value = models.FloatField()
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("compute_task_key", "metric_key"),)
