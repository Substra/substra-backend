from django.contrib.auth.hashers import make_password, check_password, is_password_usable
from django.db import models

import secrets


class Node(models.Model):
    node_id = models.CharField(primary_key=True, max_length=1024, blank=False)
    secret = models.CharField(max_length=128, blank=False)

    @staticmethod
    def generate_secret():
        return secrets.token_hex(64)

    def set_password(self, raw_secret):
        self.secret = make_password(raw_secret)
        self._secret = raw_secret

    def check_password(self, raw_secret):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_secret):
            self.set_password(raw_secret)
            # Password hash upgrades shouldn't be considered password changes.
            self._secret = None
            self.save(update_fields=["secret"])
        return check_password(raw_secret, self.secret, setter)

    class Meta:
        abstract = True


class OutgoingNode(Node):
    pass


class IncomingNode(Node):
    pass
