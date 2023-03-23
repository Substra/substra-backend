from datetime import datetime
from datetime import timedelta
from urllib.error import HTTPError

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.models.user_channel import UserChannel
from users.models.user_oidc_info import UserOidcInfo

from . import utils


class BearerTokenAuthentication(DRFTokenAuthentication):
    """
    If token is expired then it will be removed
    and new one with different key will be created
    """

    def authenticate_credentials(self, key):

        _, token = super().authenticate_credentials(key)

        is_expired = utils.bearer_token.is_token_expired(token)
        if is_expired:
            token.delete()
            raise AuthenticationFailed("The Token is expired")

        check_oidc_user_is_valid(token.user)
        return token.user, token


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


class OIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def __init__(self, *args, **kwargs):
        # this is a hack to pass refresh tokens around
        # without having to override sensitive functions
        self.refresh_token_store_hack = {}

        super().__init__(self, *args, **kwargs)

    def filter_users_by_claims(self, claims):
        """Match users based on OpenID sub"""
        openid_subject = claims.get("sub")
        issuer = claims.get("_openid_issuer")
        try:
            return (
                UserOidcInfo.objects.select_related("user")
                .get(openid_issuer=issuer, openid_subject=openid_subject)
                .user
            )
        except UserOidcInfo.DoesNotExist:
            return self.UserModel.objects.none()

    def get_token(self, payload):
        d = super().get_token(payload)
        # store it here and retrieve it in update_user
        if "refresh_token" in d:
            self.refresh_token_store_hack[d["access_token"]] = d["refresh_token"]
        return d

    def get_userinfo(self, access_token, id_token, payload):
        user_info = super().get_userinfo(access_token, id_token, payload)
        # insert issuer in user_info so it's available for filtering users
        user_info["_openid_issuer"] = payload["iss"]
        return user_info

    def get_or_create_user(self, access_token, id_token, payload):
        user = super().get_or_create_user(access_token, id_token, payload)
        # this really should be in update_user, but we don't have access to this info there
        if access_token in self.refresh_token_store_hack:
            user.oidc_info.refresh_token = self.refresh_token_store_hack[access_token]
            del self.refresh_token_store_hack[access_token]
        user.oidc_info.valid_until = _get_user_valid_until()
        user.oidc_info.save()
        return user

    def create_user(self, claims):
        email = claims.get("email")
        subject = claims.get("sub")
        issuer = claims.get("_openid_issuer")
        if settings.OIDC["USERS"]["APPEND_DOMAIN"]:
            username = utils.oidc.generate_username_with_domain(email, issuer, subject)
        else:
            username = utils.oidc.generate_username(email, issuer, subject)

        user = self.UserModel.objects.create_user(username, email=email)

        UserChannel.objects.create(user=user, channel_name=settings.OIDC["USERS"]["DEFAULT_CHANNEL"])
        UserOidcInfo.objects.create(
            user=user, openid_issuer=issuer, openid_subject=subject, valid_until=_get_user_valid_until()
        )
        return user


def _get_user_valid_until() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.OIDC["USERS"]["LOGIN_VALIDITY_DURATION"])


def _use_refresh_token(user) -> None:
    payload = {
        "client_id": settings.OIDC_RP_CLIENT_ID,
        "client_secret": settings.OIDC_RP_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": user.oidc_info.refresh_token,
    }
    response = requests.post(
        settings.OIDC_OP_TOKEN_ENDPOINT,
        data=payload,
        verify=getattr(settings, "OIDC_VERIFY_SSL", True),
        timeout=getattr(settings, "OIDC_TIMEOUT", None),
        proxies=getattr(settings, "OIDC_PROXY", None),
    )
    response.raise_for_status()

    d = response.json()

    # refresh token rotation
    if "refresh_token" in d:
        user.oidc_info.refresh_token = d["refresh_token"]

    user.oidc_info.valid_until = _get_user_valid_until()
    user.oidc_info.save()


def check_oidc_user_is_valid(user) -> None:
    """
    If the request user is an OIDC user, check their account is still valid
     -- unless it's an OIDC authentication request.
    """

    if not hasattr(user, "oidc_info"):
        return

    if not settings.OIDC["ENABLED"]:
        raise PermissionDenied("You are an OIDC user but OIDC has been disabled")

    if user.oidc_info.valid_until < datetime.now(timezone.utc):
        if user.oidc_info.refresh_token:
            try:
                _use_refresh_token(user)
                return
            except HTTPError:
                # avoid leaking info about provider
                raise PermissionDenied(
                    "You are a OIDC user but haven't authenticated in too long a time."
                    " Automated refresh attempt failed."
                    " Connect to the frontend to refresh your access."
                )
        raise PermissionDenied(
            "You are an OIDC user but haven't authenticated in too long a time,"
            " connect to the frontend to refresh your access."
        )
