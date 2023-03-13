from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import PermissionDenied
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from rest_framework_simplejwt.authentication import JWTAuthentication

from libs.expiry_token_authentication import ExpiryTokenAuthentication
from users.models.user_channel import UserChannel
from users.models.user_oidc_info import UserOidcInfo


class SecureJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        if request.resolver_match.url_name in ("user-login", "api-root"):
            return None

        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        # reconstruct token from httpOnly cookie signature
        try:
            signature = request.COOKIES["signature"]
        except Exception:
            return None
        else:
            raw_token = raw_token + f".{signature}".encode()
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            check_oidc_user_is_valid(user)
            return user, None


class ExpiryTokenAuthentication(ExpiryTokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        check_oidc_user_is_valid(user)
        return user, token


class SubstraOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        """Match users based on OpenID sub"""
        openid_subject = claims.get("sub")
        users = UserOidcInfo.objects.filter(openid_subject=openid_subject)
        if len(users) > 1:
            raise MultipleObjectsReturned(
                f"There are {len(users)} with {openid_subject=} when there should be at most one."
                f" Offending users: {users}"
            )
        if len(users) == 0:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username=users[0].user.username)

    @staticmethod
    def _get_user_valid_until() -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=settings.OIDC_USERS_LOGIN_VALIDITY_DURATION)

    def update_user(self, user, claims):
        user = super().update_user(user, claims)
        user.oidc_info.valid_until = self._get_user_valid_until()
        return user

    def create_user(self, claims):
        email = claims.get("email")
        username = self.get_username(claims)
        user = self.UserModel.objects.create_user(username, email=email)

        UserChannel.objects.create(user=user, channel_name=settings.OIDC_USERS_DEFAULT_CHANNEL)
        UserOidcInfo.objects.create(
            user=user, openid_subject=claims.get("sub"), valid_until=self._get_user_valid_until()
        )
        return user


def check_oidc_user_is_valid(user) -> None:
    """
    If the request user is an OIDC user, check their account is still valid
     -- unless it's an OIDC authentication request.
    """

    if hasattr(user, "oidc_info"):
        if not settings.OIDC_ENABLED:
            raise PermissionDenied("You are an OIDC user but OIDC has been disabled")
        if user.oidc_info.valid_until < datetime.now(timezone.utc):
            raise PermissionDenied(
                "You are an OIDC user but haven't authenticated in too long a time,"
                " connect to the frontend to refresh your access."
            )
