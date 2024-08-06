import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token


class BearerToken(Token):
    note = models.TextField(null=True)
    expires_at = models.DateTimeField(null=False, default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bearer_tokens", on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid.uuid4, editable=False)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at < timezone.now()


class ImplicitBearerToken(Token):
    """
    Separate from frontend-visible BearerTokens,
    so the behavior of /api-token-auth/ stays the same
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="implicit_bearer_tokens", on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid.uuid4, editable=False)

    @property
    def expires_at(self) -> datetime:
        return self.created + settings.EXPIRY_TOKEN_LIFETIME

    @property
    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()


@transaction.atomic
def get_implicit_bearer_token(user) -> ImplicitBearerToken:
    """
    clean up expired tokens
    """
    tokens = ImplicitBearerToken.objects.filter(user=user)
    to_delete = []
    for token in tokens:
        if token.is_expired:
            to_delete.append(token)
    for token in to_delete:
        token.delete()
    return ImplicitBearerToken.objects.create(user=user)
