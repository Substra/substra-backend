import base64
import hashlib
import logging
import re
import unicodedata

from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str

LOGGER = logging.getLogger(__name__)
ALLOWED_CHARS_RE = re.compile(r"[^a-z0-9-]")


def _sanitize(string: str) -> str:
    """
    This CAN return an empty string
    """
    string = "".join([c for c in unicodedata.normalize("NFKD", string) if not unicodedata.combining(c)])
    string = string.casefold()
    string = re.sub(ALLOWED_CHARS_RE, "-", string)
    string = re.sub(r"--+", "-", string)  # remove consecutive dashes
    string = re.sub(r"(?:^-+|-+$)", "", string)  # remove leading or trailing dashes
    return string


def _split_email_addr(addr: str) -> tuple[str, str]:
    local_part, host = addr.split("@", maxsplit=1)
    if local_part[0] == local_part[-1] == '"':
        local_part = local_part[1:-1]
    return local_part, host


def _default_username_from_email(email: str) -> str:
    username = smart_str(base64.urlsafe_b64encode(hashlib.sha1(force_bytes(email)).digest()).rstrip(b"="))
    existing_users = User.objects.filter(username=username)
    if len(existing_users) > 0:
        raise Exception(f"Default username {username} for email {email} is already taken!")
    LOGGER.warn(f"Falling back to username {username} for email {email}")
    return username


def username_with_domain_from_email(email: str) -> str:
    local_part, domain = _split_email_addr(email)
    local_part = _sanitize(local_part)
    domain = _sanitize(domain.rsplit(".", maxsplit=1)[0])

    if not local_part or not domain:
        return _default_username_from_email(email)
    username = local_part + "-" + domain
    existing_users = User.objects.filter(username=username)
    if len(existing_users) == 0:
        return username

    return _default_username_from_email(email)


def username_from_email(email: str) -> str:
    local_part, _ = _split_email_addr(email)
    username = _sanitize(local_part)

    if not username:
        return _default_username_from_email(email)
    existing_users = User.objects.filter(username=username)
    if len(existing_users) == 0:
        return username
    return _default_username_from_email(email)
