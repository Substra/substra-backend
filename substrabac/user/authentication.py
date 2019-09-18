from rest_framework_simplejwt.authentication import JWTAuthentication


class SecureJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        if request.resolver_match.url_name in ('user-login', 'api-root'):
            return None

        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        # reconstruct token from httpOnly cookie signature
        try:
            signature = request.COOKIES['signature']
        except:
            return None
        else:
            raw_token = raw_token + f".{signature}".encode()

            validated_token = self.get_validated_token(raw_token)

            return self.get_user(validated_token), None

