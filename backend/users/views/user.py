import datetime
from urllib.parse import unquote

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django_filters.rest_framework import ChoiceFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from jwt.exceptions import DecodeError
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from api.errors import BadRequestError
from api.views.filters_utils import MatchFilter
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.pagination import DefaultPageNumberPagination
from users.models.user_channel import UserChannel
from users.serializers.user import UserSerializer


def _xor_secrets(secret1, secret2):
    list = [chr(ord(s1) ^ ord(s2)) for s1, s2 in zip(secret1, secret2)]
    return "".join(list)


def _validate_token(token, secret):
    try:
        jwt.decode(token, secret, algorithms=[settings.RESET_JWT_SIGNATURE_ALGORITHM])
    except (DecodeError, ExpiredSignatureError, InvalidTokenError) as err:
        return {"is_valid": False, "message": err}

    return {"is_valid": True, "message": ""}


def _save_password(instance, password):
    serializer = UserSerializer(instance=instance, data={"password": password}, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return UserSerializer(instance=instance).data


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.channel.role == UserChannel.Role.ADMIN


class IsSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user = view.get_object()
        except BadRequestError:
            return False
        if not user.is_authenticated:
            return False

        return user.id == request.user.id


class UserFilter(FilterSet):
    role = ChoiceFilter(field_name="channel__role", choices=UserChannel.Role.choices)

    class Meta:
        model = get_user_model()
        fields = ["role"]


class UserViewSet(
    GenericViewSet,
    CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    user_model = get_user_model()
    serializer_class = UserSerializer
    pagination_class = DefaultPageNumberPagination
    ordering_fields = ["username"]
    ordering = ["username"]
    filter_backends = [OrderingFilter, MatchFilter, DjangoFilterBackend]
    lookup_field = "username"
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    search_fields = ["username"]
    filterset_class = UserFilter

    def get_queryset(self):
        channel = get_channel_name(self.request)
        return self.user_model.objects.filter(channel__channel_name=channel)

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        role = request.data.get("role")
        channel = get_channel_name(self.request)

        channel_data = {"channel_name": channel}
        if role:
            channel_data["role"] = role

        data = {"username": username, "password": password, "channel": channel_data}

        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = UserSerializer(instance=user).data

        return ApiResponse(data=data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(data))

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        role = request.data.get("role")
        ui_preferences = request.data.get("ui_preferences")
        data = {"channel": {}}

        if role:
            data["channel"]["role"] = role

        if ui_preferences:
            data["channel"]["ui_preferences"] = ui_preferences

        serializer = UserSerializer(instance=instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return ApiResponse(data=serializer.data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

    @action(methods=["put"], detail=True, permission_classes=[IsSelf])
    def password(self, request, *args, **kwargs):
        """Allows an authenticated user to modify his own password"""

        username = kwargs.get("username")
        instance = self.user_model.objects.get(username=username)
        password = request.data.get("password")

        if password:
            data = _save_password(instance, password)
            return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

        return ApiResponse(data={"message": "missing password in the request"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["post"], detail=True, permission_classes=[permissions.AllowAny], url_name="set-password")
    def set_password(self, request, *args, **kwargs):
        """Allows unauthenticated user to set new password if valid reset token is provided"""

        token = request.data.get("token")
        new_password = request.data.get("password")

        username = unquote(kwargs.get("username"))
        instance = self.user_model.objects.get(username=username)

        secret = _xor_secrets(instance.password, force_str(settings.SECRET_KEY))
        token_validation = _validate_token(token, secret)

        if token_validation.get("is_valid"):
            data = _save_password(instance, new_password)
            return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

        return ApiResponse(
            data={"message": "must provide a valid token to set a new password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @action(detail=True, permission_classes=[permissions.AllowAny], url_name="verify-token")
    def verify_token(self, request, *args, **kwargs):
        """Return 200 if reset token is valid 401 otherwise. Accepts unauthenticated request"""

        token = request.query_params.get("token", None)

        username = unquote(kwargs.get("username"))
        instance = self.user_model.objects.get(username=username)

        secret = _xor_secrets(instance.password, force_str(settings.SECRET_KEY))
        token_validation = _validate_token(token, secret)
        if token_validation.get("is_valid"):
            return ApiResponse(data={}, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

        return ApiResponse(
            data={"message": f"token not valid: {token_validation.get('message')}"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @action(methods=["post"], detail=True, url_path="reset_password", url_name="reset-password")
    def generate_reset_password_token(self, request, *args, **kwargs):
        """Returns reset password token. Restricted to Admin request"""
        instance = self.get_object()
        secret = _xor_secrets(instance.password, force_str(settings.SECRET_KEY))

        jwt_token = jwt.encode(
            payload={"exp": datetime.datetime.now() + datetime.timedelta(days=7)},
            key=secret,
            algorithm=settings.RESET_JWT_SIGNATURE_ALGORITHM,
        )

        data = {"reset_password_token": jwt_token}

        return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))
