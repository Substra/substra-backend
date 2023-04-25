from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from users.models.token import BearerToken


# this is not needed anymore ask Oliver to delete TODO
def expires_at(token: BearerToken) -> datetime:
    return timezone.now() + time_left(token)


def time_left(token: BearerToken) -> timedelta:
    time_elapsed = timezone.now() - token.created
    left_time = settings.EXPIRY_TOKEN_LIFETIME - time_elapsed
    return left_time


def is_token_expired(token: BearerToken) -> bool:
    return time_left(token) < timedelta(seconds=0)


def handle_token_expiration(token: BearerToken) -> tuple[bool, BearerToken]:
    """
    If token is expired new token will be established.
    If token is expired then it will be removed
    and new one with different key will be created
    """
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = BearerToken.objects.create(user=token.user)
    return is_expired, token
