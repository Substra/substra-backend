import re

from django.core.validators import URLValidator
from django.core.validators import _lazy_re_compile


class URLValidatorWithOptionalTLD(URLValidator):
    """
    Patch django validator to remove Top Level Domain requirement.
    For instance: `http://backend.org-1/resource` should be considered valid.
    """

    host_re = "(" + URLValidator.hostname_re + URLValidator.domain_re + ")"
    # as `host_re` value is customized, `regex` value should be rebuild
    # https://docs.djangoproject.com/en/2.2/_modules/django/core/validators/
    regex = _lazy_re_compile(
        r"^(?:[a-z0-9\.\-\+]*)://"  # scheme is validated separately
        r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
        r"(?:" + URLValidator.ipv4_re + "|" + URLValidator.ipv6_re + "|" + host_re + ")"
        r"(?::\d{2,5})?"  # port
        r"(?:[/?#][^\s]*)?"  # resource path
        r"\Z",
        re.IGNORECASE,
    )


class AssetPermissionMixin:
    def is_public(self, field: str):
        return getattr(self, f"permissions_{field}_public")

    def get_authorized_ids(self, field: str):
        return getattr(self, f"permissions_{field}_authorized_ids")

    def get_owner(self):
        return self.owner
