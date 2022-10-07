from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as djangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.state import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserChannel


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        super().validate(attrs)
        refresh = self.get_token(self.user)

        return refresh


class CustomTokenRefreshSerializer(serializers.Serializer):
    def validate(self, attrs):

        if "refresh" not in self.context["request"].COOKIES:
            raise ValidationError("refresh cookie is not present")

        refresh_cookie = self.context["request"].COOKIES["refresh"]

        refresh = RefreshToken(refresh_cookie)

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

        return refresh


class UserChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChannel
        fields = ["role", "channel_name", "ui_preferences"]

    def validate_channel_name(self, value):
        if value not in settings.LEDGER_CHANNELS:
            raise ValidationError({"channel": "Channel does not exist"})
        return value

    def validate_ui_preferences(self, value):
        if type(value) is not dict:
            raise ValidationError({"ui preferences should be a dict"})
        return value


class UserSerializer(serializers.ModelSerializer):
    channel = UserChannelSerializer()

    class Meta:
        model = User
        fields = ["username", "password", "channel"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        if not value:
            raise ValidationError("Missing password")
        try:
            validate_password(value, self)
        except djangoValidationError as err:
            raise ValidationError(err.error_list)
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError("Username already exists")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        channel = data.pop("channel")
        for key in channel:
            if key == "channel_name":
                data["channel"] = channel[key]
            else:
                data[key] = channel[key]
        return data

    def create(self, validated_data):
        channel_data = validated_data.pop("channel")
        user = User.objects.create_user(**validated_data)
        UserChannel.objects.create(user=user, **channel_data)
        return user

    def _update_ui_preferences(self, instance, value):
        ui_preferences = instance.channel.ui_preferences
        if not ui_preferences:
            ui_preferences = {}
        if value:
            for key in value:
                ui_preferences[key] = value[key]
        return ui_preferences

    def update(self, instance, validated_data):
        password = validated_data.get("password")
        if password:
            instance.set_password(password)

        channel = validated_data.get("channel")
        if channel:
            instance.channel.role = validated_data.get("channel").get("role", instance.channel.role)
            instance.channel.ui_preferences = self._update_ui_preferences(
                instance, validated_data.get("channel").get("ui_preferences", instance.channel.ui_preferences)
            )
            instance.channel.save()

        instance.save()
        return instance
