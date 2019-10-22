from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import IncomingNode


class NodeUser(User):
    pass


# TODO: should be removed when node to node authent will be done via certificates
class NodeBackend:
    """Authenticate node """

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        if not username or not password:
            return None

        try:
            node = IncomingNode.objects.get(node_id=username)
        except ObjectDoesNotExist:
            return None
        else:
            if node.check_password(password):
                return NodeUser(username=username)

            return None

    def get_user(self, user_id):
        # required for session
        return None
