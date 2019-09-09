from django.conf import settings
from django.contrib.auth.models import User


class SettingsBackend:
    """Authenticate against user and password defined in settings."""

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        if not username or not password:
            return None

        if username == settings.BASICAUTH_USERNAME and password == settings.BASICAUTH_PASSWORD:
            return User(username=username)

        return None

    def get_user(self, user_id):
        # required for session
        return None
