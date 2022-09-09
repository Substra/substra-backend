from django.db import models


class DataSampleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("data_sample_task__order")


class DataSample(models.Model):
    """Datasample represent a datasample and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)
    test_only = models.BooleanField()
    data_managers = models.ManyToManyField("DataManager", related_name="data_samples", related_query_name="data_sample")
    objects = DataSampleManager()

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
