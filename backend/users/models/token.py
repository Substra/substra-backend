import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from rest_framework.authtoken.models import Token


class BearerToken(Token):
    note = models.TextField(null=True)
    expiry = models.DateTimeField(null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bearer_tokens", on_delete=models.CASCADE, verbose_name=("Users")
    )
    token_id = models.UUIDField(default=uuid.uuid4, editable=False)

    @property
    def is_expired(self) -> bool:
        if self.expiry is None:
            return False
        return self.expiry < timezone.now()
