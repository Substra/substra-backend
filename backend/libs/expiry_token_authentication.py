from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from datetime import timedelta
from django.utils import timezone


# this return left time
def expires_at(token):
    time_elapsed = timezone.now() - token.created
    left_time = getattr(settings, 'EXPIRY_TOKEN_LIFETIME') - time_elapsed
    return left_time


# token checker if token expired or not
def is_token_expired(token):
    return expires_at(token) < timedelta(seconds=0)


# if token is expired new token will be established
# If token is expired then it will be removed
# and new one with different key will be created
def token_expire_handler(token):
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

        _, token = super(ExpiryTokenAuthentication, self).authenticate_credentials(key)

        is_expired = is_token_expired(token)
        if is_expired:
            token.delete()
            raise AuthenticationFailed('The Token is expired')

        return token.user, token
