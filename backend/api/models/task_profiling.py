from django.db import models


class ProfilingStep(models.Model):
    """A profiling step"""

    compute_task_profile = models.ForeignKey(
        "TaskProfiling", on_delete=models.CASCADE, related_name="execution_rundown"
    )
    step = models.CharField(max_length=100)
    duration = models.DurationField()

    class Meta:
        unique_together = (("compute_task_profile", "step"),)
        ordering = ["step"]


class TaskProfiling(models.Model):
    """Task profiling data table"""

    compute_task = models.OneToOneField(
        "ComputeTask", primary_key=True, on_delete=models.CASCADE, related_name="task_profiling"
    )
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creation_date"]
