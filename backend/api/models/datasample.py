from django.db import models


class DataSample(models.Model):
    """Datasample represent a datasample and its associated metadata"""

    key = models.UUIDField(primary_key=True)
    owner = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)
    data_managers = models.ManyToManyField("DataManager", related_name="data_samples", related_query_name="data_sample")

    class Meta:
        ordering = ["creation_date", "key"]  # default order for relations serializations
