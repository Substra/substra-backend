from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import IncomingOrganization


class OrganizationUser(User):
    pass


# TODO: should be removed when organization to organization authent will be done via certificates
class OrganizationBackend(BaseBackend):
    """Authenticate organization"""

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a user."""
        if not username or not password:
            return None

        try:
            organization = IncomingOrganization.objects.get(organization_id=username)
        except ObjectDoesNotExist:
            return None
        else:
            if organization.check_password(password):
                return OrganizationUser(username=username)

            return None

    def get_user(self, user_id):
        # required for session
        return None
