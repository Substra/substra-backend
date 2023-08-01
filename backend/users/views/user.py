import datetime
import json
from urllib.parse import unquote

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as djangoValidationError
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
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from api.errors import BadRequestError
from api.views.filters_utils import MatchFilter
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.pagination import DefaultPageNumberPagination
from libs.permissions import IsAuthorized
from users.models.user_channel import UserChannel
from users.serializers.user import UserAwaitingApprovalSerializer
from users.serializers.user import UserSerializer


def _xor_secrets(secret1, secret2):
    list = [chr(ord(s1) ^ ord(s2)) for s1, s2 in zip(secret1, secret2)]
    return "".join(list)


def _validate_channel(name):
    if name not in settings.LEDGER_CHANNELS:
        raise ValidationError({"channel": "Channel does not exist"})


def _validate_password(password, user):
    if not password:
        raise ValidationError("Missing password")
    try:
        validate_password(password, user)
    except djangoValidationError as err:
        raise ValidationError(err.error_list)


def _validate_username(username):
    user_model = get_user_model()
    if user_model.objects.filter(username=username).exists():
        raise BadRequestError("Username already exists")


def _validate_role(role):
    try:
        role = UserChannel.Role[role]
        return role
    except KeyError:
        raise ValidationError({"role": "Invalid role"})


def _validate_token(token, secret):
    try:
        jwt.decode(token, secret, algorithms=[settings.RESET_JWT_SIGNATURE_ALGORITHM])
    except (DecodeError, ExpiredSignatureError, InvalidTokenError) as err:
        return {"is_valid": False, "detail": err}

    return {"is_valid": True, "detail": ""}


def _save_password(view, instance, password):
    _validate_password(password, view.user_model(username=instance.username))
    instance.set_password(password)
    instance.save()
    return UserSerializer(instance=instance).data


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.channel.role == UserChannel.Role.ADMIN


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.channel.role == UserChannel.Role.ADMIN


class IsSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        user = view.get_object()
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
    permission_classes = [IsAuthorized, IsAdminOrReadOnly]
    search_fields = ["username"]
    filterset_class = UserFilter

    def get_queryset(self):
        channel = get_channel_name(self.request)
        return self.user_model.objects.filter(channel__channel_name=channel)

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        channel = get_channel_name(self.request)
        role = request.data.get("role")

        _validate_channel(channel)
        _validate_username(username)
        _validate_password(password, self.user_model(username=username))

        channel_data = {"channel_name": channel}
        if role:
            channel_data["role"] = _validate_role(role)

        user = self.user_model.objects.create_user(username=username, password=password)

        channel_data["user"] = user

        UserChannel.objects.create(**channel_data)

        user.refresh_from_db()
        data = UserSerializer(instance=user).data

        return ApiResponse(data=data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(data))

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        role = request.data.get("role")

        if role:
            role = _validate_role(role)
            instance.channel.role = role
            instance.channel.save()

        instance.save()
        data = UserSerializer(instance=instance).data

        return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

    @action(methods=["put"], detail=True, permission_classes=[IsSelf])
    def password(self, request, *args, **kwargs):
        """Allows an authenticated user to modify his own password"""
        instance = self.get_object()
        password = request.data.get("password")

        if password:
            data = _save_password(self, instance, password)
            return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

        return ApiResponse(data={"detail": "missing password in the request"}, status=status.HTTP_400_BAD_REQUEST)

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
            data = _save_password(self, instance, new_password)
            return ApiResponse(data=data, status=status.HTTP_200_OK, headers=self.get_success_headers({}))

        return ApiResponse(
            data={"detail": "must provide a valid token to set a new password"},
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
            data={"detail": f"token not valid: {token_validation.get('detail')}"},
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


class UserAwaitingApprovalViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
):
    user_model = get_user_model()
    permission_classes = [IsAdmin]
    pagination_class = DefaultPageNumberPagination
    serializer_class = UserAwaitingApprovalSerializer
    ordering_fields = ["username"]
    ordering = ["username"]
    filter_backends = [OrderingFilter, MatchFilter, DjangoFilterBackend]
    lookup_field = "username"
    search_fields = ["username"]
    filterset_class = UserFilter

    def get_queryset(self):
        return self.user_model.objects.filter(channel=None).exclude(username__in=settings.VIRTUAL_USERNAMES.values())

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(username=request.GET.get("username"))
            user.delete()
            return ApiResponse(data={"detail": "User removed"}, status=status.HTTP_200_OK)
        except User.DoesNotExist or User.MultipleObjectsReturned:
            pass
        return ApiResponse(data={"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, *args, **kwargs):
        d = json.loads(request.body)
        try:
            user = User.objects.get(username=request.GET.get("username"))
        except User.DoesNotExist:
            return ApiResponse(data={"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.MultipleObjectsReturned:
            return ApiResponse(
                data={"detail": "Multiple instance of the same user found"}, status=status.HTTP_409_CONFLICT
            )

        channel_name = get_channel_name(request)
        channel_name = get_channel_name(request)
        role = _validate_role(d.get("role"))
        UserChannel.objects.create(channel_name=channel_name, role=role, user=user)
        data = UserSerializer(instance=user).data
        return ApiResponse(data=data, status=status.HTTP_200_OK)
