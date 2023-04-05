from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.hashers import make_password
from django.db import models


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
