from django.db import models


class LastEvent(models.Model):
    channel = models.CharField(max_length=100, primary_key=True)
    event_id = models.CharField(max_length=250, default="", null=True, blank=True)
