from django.db import models


class ChannelOrganization(models.Model):
    organization_id = models.CharField(max_length=64)
    address = models.CharField(max_length=200, default="")
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        ordering = ["organization_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "channel"],
                name="unique_id_for_channel",
            ),
        ]
