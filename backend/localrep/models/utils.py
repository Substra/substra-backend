import re

from django.core.validators import URLValidator
from django.core.validators import _lazy_re_compile
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper


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


def get_enum_choices(proto_enum: EnumTypeWrapper) -> list[tuple[str, int]]:
    """
    Get model choices from protobuf enum.
    """
    return [(name, value) for (value, name) in proto_enum.items()]
