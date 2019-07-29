from django.db import models

from authent.models.node import Node


class ExternalAuthent(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    username = models.CharField(max_length=256)
    password = models.CharField(max_length=256)

    def __str__(self):
        # TODO
        return self.node.name
