from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed

from users.serializers import CustomTokenObtainPairSerializer

import tldextract


class UserViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CustomTokenObtainPairSerializer

    www_authenticate_realm = 'api'

    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def get_host(self, request):
        ext = tldextract.extract(request.get_host())
        host = ext.domain
        if ext.suffix:
            host += '.' + ext.suffix

        return host

    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return Response({'message': 'wrong username password'}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        token = serializer.validated_data

        expires = token.current_time + token.lifetime

        tokenString = str(token)
        headerPayload = '.'.join(tokenString.split('.')[0:2])
        signature = tokenString.split('.')[2]

        response = Response(token.payload, status=status.HTTP_200_OK)

        host = self.get_host(request)

        if settings.DEBUG:
            response.set_cookie('header.payload', value=headerPayload, expires=expires, domain=host)
            response.set_cookie('signature', value=signature, httponly=True, domain=host)
        else:
            response.set_cookie('header.payload', value=headerPayload, expires=expires, secure=True, domain=host)
            response.set_cookie('signature', value=signature, httponly=True, secure=True, domain=host)
        return response

    @action(detail=False)
    def logout(self, request, *args, **kwargs):
        response = Response({}, status=status.HTTP_200_OK)

        host = self.get_host(request)
        if settings.DEBUG:
            response.set_cookie('header.payload', value='', domain=host)
            response.set_cookie('signature', value='', httponly=True, domain=host)
        else:
            response.set_cookie('header.payload', value='', secure=True, domain=host)
            response.set_cookie('signature', value='', httponly=True, secure=True, domain=host)
        return response
