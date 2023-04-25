import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from rest_framework.authtoken.models import Token


class BearerToken(Token):
    note = models.TextField(default=None, null=True)
    # for now it is a date time field but a lenght could also be smart
    expiry = models.DateTimeField(default=None, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bearer_tokens", on_delete=models.CASCADE, verbose_name=("Users")
    )
    token_id = models.UUIDField(default=uuid.uuid4, editable=False)

    def expires_at(self) -> models.DateTimeField:
        return self.expiry

    def is_token_expired(self) -> bool:
        if self.expiry is None:
            return False
        return self.time_left() < timedelta(seconds=0)

    def time_left(self):
        if self.expiry is None:
            return None
        left_time: timedelta = self.expiry - self.created
        return left_time
