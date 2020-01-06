from rest_framework.authentication import SessionAuthentication


class CustomSessionAuthentication(SessionAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # bypass for login with jwt
        if request.resolver_match.url_name == 'user-login':
            return None

        return super(CustomSessionAuthentication, self).authenticate(request)
