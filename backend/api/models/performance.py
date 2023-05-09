from django.db import models


class Performance(models.Model):
    compute_task_output = models.ForeignKey(
        "ComputeTaskOutput", on_delete=models.deletion.DO_NOTHING, related_name="performances"
    )
    value = models.FloatField()
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)
