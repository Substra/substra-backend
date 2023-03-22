import base64
import hashlib
import logging
import re
import unicodedata

from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str

LOGGER = logging.getLogger(__name__)
ALLOWED_CHARS_REGEX = re.compile(r"[^a-z0-9-]")

"""
Creating a username from an email is used for OIDC accounts
"""


def _sanitize(string: str) -> str:
    """
    This CAN return an empty string
    """
    string = "".join([c for c in unicodedata.normalize("NFKD", string) if not unicodedata.combining(c)])
    string = string.casefold()
    string = re.sub(ALLOWED_CHARS_REGEX, "-", string)
    string = re.sub(r"--+", "-", string)  # remove consecutive dashes
    string = re.sub(r"(?:^-+|-+$)", "", string)  # remove leading or trailing dashes
    return string


def _split_email_addr(addr: str) -> tuple[str, str]:
    """
    No validation, it should accept all valid emails but also some invalid ones
    """
    local_part, host = addr.rsplit("@", maxsplit=1)
    if local_part[0] == local_part[-1] == '"':
        local_part = local_part[1:-1]
    if host[0] == "[" and host[-1] == "]":
        host = host[1:-1]
    return local_part, host


def _iterate_username(proposed_username: str) -> str:
    """append a number to an already taken username"""
    existing_users = list(
        User.objects.filter(username__startswith=proposed_username).values_list("username", flat=True)
    )
    sanity_limit = 100
    for iter in range(2, sanity_limit):
        if f"{proposed_username}-{iter}" not in existing_users:
            return f"{proposed_username}-{iter}"
    raise Exception(f"{sanity_limit} people seem to share the username {proposed_username}")


class OIDC:
    @staticmethod
    def _generate_default_username(email: str, issuer: str, subject: str) -> str:
        # issuer+subject should be unique but let's not leak this info
        username = smart_str(
            base64.urlsafe_b64encode(hashlib.sha256(force_bytes(issuer + subject)).digest()).rstrip(b"=")
        )
        if User.objects.filter(username=username).exists():
            raise Exception(f"User {username} already exists")
        LOGGER.warning(f"Falling back to username {username} for email {email}")
        return username

    @staticmethod
    def generate_username_with_domain(email: str, issuer: str, subject: str) -> str:
        local_part, domain = _split_email_addr(email)
        local_part = _sanitize(local_part)
        domain = _sanitize(domain.rsplit(".", maxsplit=1)[0])

        if not local_part or not domain:
            return OIDC._generate_default_username(email, issuer, subject)
        username = local_part + "-" + domain
        if not User.objects.filter(username=username).exists():
            return username
        return _iterate_username(username)

    @staticmethod
    def generate_username(email: str, issuer: str, subject: str) -> str:
        local_part, _ = _split_email_addr(email)
        username = _sanitize(local_part)

        if not username:
            return OIDC._generate_default_username(email, issuer, subject)
        if not User.objects.filter(username=username).exists():
            return username
        return _iterate_username(username)
