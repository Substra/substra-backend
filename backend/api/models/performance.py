from django.db import models


class Performance(models.Model):
    metric = models.ForeignKey("Function", on_delete=models.deletion.DO_NOTHING, related_name="performances")
    compute_task_output = models.ForeignKey(
        "ComputeTaskOutput", on_delete=models.deletion.DO_NOTHING, related_name="performances"
    )
    value = models.FloatField()
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        unique_together = (("compute_task_output", "metric"),)
