from django.db import models
from django.contrib.auth.models import User

import secrets


class Node(models.Model):
    node_id = models.CharField(primary_key=True, max_length=1024, blank=False)
    secret = models.CharField(max_length=128, blank=False)

    @staticmethod
    def generate_secret():
        return secrets.token_hex(64)

    class Meta:
        abstract = True


class OutgoingNode(Node):
    pass


class IncomingNode(Node):
    pass
