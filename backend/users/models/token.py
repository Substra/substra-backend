import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token


class BearerToken(Token):
    note = models.TextField(null=True)
    expires_at = models.DateTimeField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bearer_tokens", on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid.uuid4, editable=False)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at < timezone.now()


class ImplicitBearerToken(Token):
    """
    Legacy token to make the endpoint api-token-auth/ work like it used to
    """

    @property
    def expires_at(self) -> datetime:
        return self.created + settings.EXPIRY_TOKEN_LIFETIME

    @property
    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()

    @transaction.atomic
    def handle_expiration(self) -> "ImplicitBearerToken":
        """
        If token is expired a new token will be created and the old one removed.
        """
        if self.is_expired:
            user = self.user
            self.delete()
            token = ImplicitBearerToken.objects.create(user=user)
            return token
        return self
