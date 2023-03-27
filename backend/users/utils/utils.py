import re
import unicodedata

from django.contrib.auth.models import User

ALLOWED_CHARS_REGEX = re.compile(r"[^a-z0-9-]")

"""
Creating a username from an email is used for OIDC accounts
"""


def sanitize(string: str) -> str:
    """
    This CAN return an empty string
    """
    string = "".join([c for c in unicodedata.normalize("NFKD", string) if not unicodedata.combining(c)])
    string = string.casefold()
    string = re.sub(ALLOWED_CHARS_REGEX, "-", string)
    string = re.sub(r"--+", "-", string)  # remove consecutive dashes
    string = re.sub(r"(?:^-+|-+$)", "", string)  # remove leading or trailing dashes
    return string


def split_email_addr(addr: str) -> tuple[str, str]:
    """
    No validation, it should accept all valid emails but also some invalid ones
    """
    local_part, host = addr.rsplit("@", maxsplit=1)
    if local_part[0] == local_part[-1] == '"':
        local_part = local_part[1:-1]
    if host[0] == "[" and host[-1] == "]":
        host = host[1:-1]
    return local_part, host


def iterate_username(proposed_username: str) -> str:
    """append a number to an already taken username"""
    existing_users = list(
        User.objects.filter(username__startswith=proposed_username).values_list("username", flat=True)
    )
    sanity_limit = 100
    for iter in range(2, sanity_limit):
        if f"{proposed_username}-{iter}" not in existing_users:
            return f"{proposed_username}-{iter}"
    raise Exception(f"{sanity_limit} people seem to share the username {proposed_username}")
