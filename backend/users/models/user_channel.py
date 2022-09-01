from django.conf import settings
from django.db import models


class UserChannel(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN"
        USER = "USER"

    role = models.CharField(
        max_length=64,
        choices=Role.choices,
        default=Role.USER,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, parent_link=True, on_delete=models.CASCADE, related_name="channel"
    )
    channel_name = models.CharField(max_length=100)
