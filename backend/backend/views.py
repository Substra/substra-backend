from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle

from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from libs.expiry_token_authentication import expires_at
from libs.user_login_throttle import UserLoginThrottle


class ExpiryObtainAuthToken(ObtainAuthToken):
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserLoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # token should be new each time, remove the old one
        # Token.objects.filter(user=user).delete()
        # token = Token.objects.create(user=user)
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'expires_at': expires_at(token)
        })


obtain_auth_token = ExpiryObtainAuthToken.as_view()
