from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.decorators import throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from libs.user_login_throttle import UserLoginThrottle
from users.serializers import CustomTokenObtainPairSerializer
from users.serializers import CustomTokenRefreshSerializer


def set_token_cookies(response: Response, refresh_token) -> None:

    access_token = refresh_token.access_token

    access_expires = access_token.current_time + access_token.lifetime
    refresh_expires = refresh_token.current_time + refresh_token.lifetime

    access_token_string = str(access_token)
    header_payload = ".".join(access_token_string.split(".")[0:2])
    signature = access_token_string.split(".")[2]

    secure = not settings.DEBUG

    response.set_cookie(
        "header.payload",
        value=header_payload,
        expires=access_expires,
        secure=secure,
        domain=settings.COMMON_HOST_DOMAIN,
    )
    response.set_cookie(
        "signature",
        value=signature,
        expires=access_expires,
        httponly=True,
        secure=secure,
        domain=settings.COMMON_HOST_DOMAIN,
    )
    response.set_cookie(
        "refresh",
        value=str(refresh_token),
        expires=refresh_expires,
        httponly=True,
        secure=secure,
        domain=settings.COMMON_HOST_DOMAIN,
    )


class AuthenticationViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CustomTokenObtainPairSerializer

    www_authenticate_realm = "api"

    permission_classes = [AllowAny]

    def get_authenticate_header(self, request) -> str:
        return f'{AUTH_HEADER_TYPES[0]} realm="{self.www_authenticate_realm}"'

    @action(methods=["post"], detail=False)
    @throttle_classes([AnonRateThrottle, UserLoginThrottle])
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return Response({"message": "wrong username password"}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        data = serializer.validated_data

        refresh_token = data
        access_token = data.access_token

        response = Response(access_token.payload, status=status.HTTP_200_OK)

        set_token_cookies(response, refresh_token)

        return response

    @action(methods=["post"], detail=False)
    def refresh(self, request, *args, **kwargs):
        serializer = CustomTokenRefreshSerializer(data=request.data, context=self.get_serializer_context())
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return Response({"message": "wrong username password"}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        data = serializer.validated_data

        refresh_token = data
        access_token = data.access_token

        response = Response(access_token.payload, status=status.HTTP_200_OK)

        set_token_cookies(response, refresh_token)

        return response

    @action(detail=False)
    def logout(self, request, *args, **kwargs):
        # Blacklist jwt token at logout fetched from cookie
        if "refresh" in request.COOKIES:
            refresh = RefreshToken(request.COOKIES["refresh"])
            try:
                # Attempt to blacklist the fetched refresh token
                refresh.blacklist()
            except AttributeError:
                # If blacklist app not installed, `blacklist` method will
                # not be present
                pass

        response = Response({}, status=status.HTTP_200_OK)

        response.delete_cookie("header.payload", domain=settings.COMMON_HOST_DOMAIN)
        response.delete_cookie("signature", domain=settings.COMMON_HOST_DOMAIN)
        response.delete_cookie("refresh", domain=settings.COMMON_HOST_DOMAIN)

        return response


class OIDCAuthenticationCallbackJwtView(OIDCAuthenticationCallbackView):
    """
    The default OIDCAuthenticationCallbackView logs a user in via session, but this instead sets cookies as higher up

    based on source:
    https://github.com/mozilla/mozilla-django-oidc/blob/71e4af8283a10aa51234de705d34cd298e927f97/mozilla_django_oidc/views.py#L45
    """

    def login_success(self):
        user = getattr(self.request, "user", None)

        # if DEBUG, also log in via the session so we can use DRF's API browser
        if settings.DEBUG:
            # If the user hasn't changed (because this is a session refresh instead of a
            # normal login), don't call login. This prevents invaliding the user's current CSRF token
            if not user or not user.is_authenticated or user != self.user:
                auth.login(self.request, self.user)

        refresh_token = RefreshToken.for_user(self.user)
        access_token = refresh_token.access_token

        response = HttpResponseRedirect(self.success_url, access_token.payload)
        # FIXME we should change how we hand out tokens based on the OpenID token?
        set_token_cookies(response, refresh_token)

        return response
