from django.db import models


class ChannelNode(models.Model):
    node_id = models.CharField(max_length=64)
    creation_date = models.DateTimeField()
    channel = models.CharField(max_length=100)

    class Meta:
        ordering = ["node_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["node_id", "channel"],
                name="unique_id_for_channel",
            ),
        ]
