from django.db import models


class Performance(models.Model):
    compute_task = models.ForeignKey("ComputeTask", on_delete=models.deletion.DO_NOTHING, related_name="performances")
    metric = models.ForeignKey("Metric", on_delete=models.deletion.DO_NOTHING, related_name="performances")
    value = models.FloatField()
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("compute_task", "metric"),)
