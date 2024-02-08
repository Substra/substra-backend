from django.db import models


class ImageEntrypoint(models.Model):
    """The container image entrypoint of an Function or a Metric"""

    archive_checksum = models.CharField(primary_key=True, editable=False, max_length=256, default="invalid")
    entrypoint_json = models.JSONField()
    creation_date = models.DateTimeField(auto_now_add=True)
