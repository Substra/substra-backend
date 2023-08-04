from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied


class ImplicitLoginDisabled(PermissionDenied):
    default_detail = _("Implicit login is disabled on this server")
    substra_identifier = "implicit_login_disabled"
