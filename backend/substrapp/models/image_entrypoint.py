from django.db import models


class ImageEntrypoint(models.Model):
    """The container image entrypoint of an Algo or a Metric"""

    asset_key = models.UUIDField(primary_key=True, editable=False)
    entrypoint_json = models.JSONField()
    creation_date = models.DateTimeField(auto_now_add=True)
