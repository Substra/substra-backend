import secrets

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.hashers import make_password
from django.db import models


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


# Manager allowing an extra parameter, 'password', to hash passwords
class IncomingOrganizationManager(models.Manager):
    def create(self, **obj_data):

        password = obj_data.pop("password", None)
        secret = obj_data.get("secret", None)

        if password and secret:
            raise ValueError(
                "password and secret cannot be set at the same time. "
                "Set argument 'password' to provide an unhashed password and 'secret' for a hashed one"
            )

        if secret:
            try:
                identify_hasher(secret)
            except ValueError:
                raise ValueError(
                    "Cannot identify the hasher required for the argument 'secret'. "
                    "If you try to provide an unhashed password, use the argument 'password' instead"
                )

        if password:
            obj_data["secret"] = make_password(password)

        # Now call the super method which does the actual creation
        return super(IncomingOrganizationManager, self).create(**obj_data)


class IncomingOrganization(Organization):
    objects = IncomingOrganizationManager()
