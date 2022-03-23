from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


def expires_at(token):
    """Return time left."""
    time_elapsed = timezone.now() - token.created
    left_time = settings.EXPIRY_TOKEN_LIFETIME - time_elapsed
    return left_time


def is_token_expired(token):
    """Check whether token has expired or not"""
    return expires_at(token) < timedelta(seconds=0)


def token_expire_handler(token):
    """
    If token is expired new token will be established.
    If token is expired then it will be removed
    and new one with different key will be created
    """
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = Token.objects.create(user=token.user)
    return is_expired, token


class ExpiryTokenAuthentication(TokenAuthentication):
    """
    If token is expired then it will be removed
    and new one with different key will be created
    """

    def authenticate_credentials(self, key):

        _, token = super().authenticate_credentials(key)

        is_expired = is_token_expired(token)
        if is_expired:
            token.delete()
            raise AuthenticationFailed("The Token is expired")

        return token.user, token
