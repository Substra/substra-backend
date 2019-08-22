from django.db import models
from django.contrib.auth.models import AbstractUser


class Node(models.Model):
    node_id = models.CharField(primary_key=True, max_length=64, blank=False)
    secret = models.CharField(max_length=128, blank=False)

    class Meta:
        abstract = True


class OutgoingNode(Node):
    pass


class IncomingNode(Node):
    pass
