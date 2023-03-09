from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from rest_framework_simplejwt.authentication import JWTAuthentication

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

            return self.get_user(validated_token), None


class SubstraOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        """Match users based on OpenID sub"""
        openid_subject = claims.get("sub")
        users = UserOidcInfo.objects.filter(openid_subject=openid_subject)
        if len(users) > 1:
            raise Exception(
                f"There are {len(users)} with {openid_subject=} when there should be at most one."
                f" Offending users: {users}"
            )
        if len(users) == 0:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username=users[0].user.username)

    def create_user(self, claims):
        email = claims.get("email")
        username = self.get_username(claims)
        user = self.UserModel.objects.create_user(username, email=email)

        UserChannel.objects.create(user=user, channel_name=settings.OIDC_USERS_DEFAULT_CHANNEL)
        UserOidcInfo.objects.create(user=user, openid_subject=claims.get("sub"))
        return user
