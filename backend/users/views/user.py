from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed

from users.serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer

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

        data = serializer.validated_data

        refresh_token = data
        access_token = data.access_token

        access_expires = access_token.current_time + access_token.lifetime
        refresh_expires = refresh_token.current_time + refresh_token.lifetime

        access_token_string = str(access_token)
        header_payload = '.'.join(access_token_string.split('.')[0:2])
        signature = access_token_string.split('.')[2]

        response = Response(access_token.payload, status=status.HTTP_200_OK)

        host = self.get_host(request)

        secure = not settings.DEBUG

        response.set_cookie('header.payload', value=header_payload, expires=access_expires, secure=secure, domain=host)
        response.set_cookie('signature', value=signature, httponly=True, secure=secure, domain=host)
        response.set_cookie('refresh', value=str(refresh_token), expires=refresh_expires, httponly=True, secure=secure,
                            domain=host)

        return response

    @action(methods=['post'], detail=False)
    def refresh(self, request, *args, **kwargs):
        serializer = CustomTokenRefreshSerializer(data=request.data, context=self.get_serializer_context())

        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return Response({'message': 'wrong username password'}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        data = serializer.validated_data

        refresh_token = data
        access_token = data.access_token

        access_expires = access_token.current_time + access_token.lifetime
        refresh_expires = refresh_token.current_time + refresh_token.lifetime

        access_token_string = str(access_token)
        header_payload = '.'.join(access_token_string.split('.')[0:2])
        signature = access_token_string.split('.')[2]

        response = Response(access_token.payload, status=status.HTTP_200_OK)

        host = self.get_host(request)

        secure = not settings.DEBUG

        response.set_cookie('header.payload', value=header_payload, expires=access_expires, secure=secure, domain=host)
        response.set_cookie('signature', value=signature, httponly=True, secure=secure, domain=host)
        response.set_cookie('refresh', value=str(refresh_token), expires=refresh_expires, httponly=True, secure=secure,
                            domain=host)

        return response

    @action(detail=False)
    def logout(self, request, *args, **kwargs):
        response = Response({}, status=status.HTTP_200_OK)

        host = self.get_host(request)

        response.delete_cookie('header.payload', domain=host)
        response.delete_cookie('signature', domain=host)
        response.delete_cookie('refresh', domain=host)

        return response
