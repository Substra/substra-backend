import os
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle

from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from libs.expiry_token_authentication import token_expire_handler, expires_at
from libs.user_login_throttle import UserLoginThrottle

from rest_framework.views import APIView
from substrapp.views.utils import get_channel_name
from django.conf import settings


class ExpiryObtainAuthToken(ObtainAuthToken):
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserLoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if os.environ.get('TOKEN_STRATEGY', 'unique') == 'reuse':
            token, created = Token.objects.get_or_create(user=user)

            # token_expire_handler will check, if the token is expired it will generate new one
            is_expired, token = token_expire_handler(token)

        else:
            # token should be new each time, remove the old one
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)

        return Response({
            'token': token.key,
            'expires_at': expires_at(token)
        })


class Info(APIView):

    def get(self, request, *args, **kwargs):
        channel_name = get_channel_name(request)
        channel = settings.LEDGER_CHANNELS[channel_name]
        return Response({
            'host': settings.DEFAULT_DOMAIN,
            'channel': channel_name,
            'config': {
                'model_export_enabled': channel['model_export_enabled'],
            }
        })


obtain_auth_token = ExpiryObtainAuthToken.as_view()
info_view = Info.as_view()
