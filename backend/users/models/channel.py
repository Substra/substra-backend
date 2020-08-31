from django.conf import settings
from django.db import models


class Channel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        parent_link=True,
        on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
