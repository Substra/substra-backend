from django.conf import settings
from django.contrib.auth.models import User


class SettingsBackend:
    """Authenticate against user and password defined in settings."""

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        if not username or not password:
            return None

        server_username = settings.BASICAUTH_USERNAME
        server_password = settings.BASICAUTH_PASSWORD
        if username == server_username and password == server_password:
            return User(username)

        return None

    def get_user(self, user_id):
        # required for session
        return None
