import secrets

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import models

from organization.managers import IncomingOrganizationManager


class Organization(models.Model):
    organization_id = models.CharField(primary_key=True, max_length=1024, blank=False)
    secret = models.CharField(max_length=128, blank=False)

    @staticmethod
    def generate_password():
        return secrets.token_hex(64)

    def set_password(self, raw_secret):
        self.secret = make_password(raw_secret)

    def check_password(self, raw_secret):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_secret):
            self.set_password(raw_secret)
            self.save(update_fields=["secret"])

        return check_password(raw_secret, self.secret, setter)

    class Meta:
        abstract = True


class OutgoingOrganization(Organization):
    pass


class IncomingOrganization(Organization):
    objects = IncomingOrganizationManager()
