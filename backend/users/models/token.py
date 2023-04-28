import uuid
from datetime import datetime
from datetime import timedelta

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


class ImplicitBearerToken(Token):
    """
    Legacy token to make the endpoint api-token-auth/ work like it used to
    """

    @property
    def expiry(self) -> datetime:
        return timezone.now() + self.time_left

    @property
    def time_left(self) -> timedelta:
        time_elapsed = timezone.now() - self.created
        left_time = settings.EXPIRY_TOKEN_LIFETIME - time_elapsed
        return left_time

    @property
    def is_expired(self) -> bool:
        return self.time_left < timedelta(seconds=0)

    def handle_expiration(self) -> "ImplicitBearerToken":
        """
        If token is expired new token will be established.
        If token is expired then it will be removed
        and new one with different key will be created
        """
        if self.is_expired:
            self.delete()
            token = ImplicitBearerToken.objects.create(user=self.user)
            return token
        return self
