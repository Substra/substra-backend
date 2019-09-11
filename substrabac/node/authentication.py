from django.contrib.auth.models import User
from .models import IncomingNode


class NodeUser(User):
    pass


# TODO: should be removed when node to node authent will be done via certificates
class NodeBackend:
    """Authenticate node """

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        node_id = username
        secret = password

        if not node_id or not secret:
            return None

        incoming_node_exists = IncomingNode.objects.filter(node_id=node_id, secret=secret).exists()
        if incoming_node_exists:
            return NodeUser(username=node_id)

        return None

    def get_user(self, user_id):
        # required for session
        return None
