from django.contrib.auth.models import User
from .models import IncomingNode


class NodeBackend:
    """Authenticate node """

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        node_id = username
        secret = password

        if not node_id or not secret:
            return None

        incoming_node = IncomingNode.objects.get(node_id=node_id)
        if not incoming_node:
            return None

        if node_id == incoming_node.node_id and secret == incoming_node.secret:
            return User(node_id)

        return None

    def get_user(self, user_id):
        # required for session
        return None
