from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.utils import datetime_from_epoch


class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    def get_token(self, user):
        """
        Adds this token to the outstanding token list.
        """
        token = AccessToken.for_user(user)

        jti = token[api_settings.JTI_CLAIM]
        exp = token['exp']

        OutstandingToken.objects.create(
            user=user,
            jti=jti,
            token=str(token),
            created_at=token.current_time,
            expires_at=datetime_from_epoch(exp),
        )

        return token

    def validate(self, attrs):
        super().validate(attrs)
        token = self.get_token(self.user)

        return token
