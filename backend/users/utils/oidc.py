import base64
import hashlib
import logging

from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str

from . import utils

LOGGER = logging.getLogger(__name__)


def _generate_default_username(email: str, issuer: str, subject: str) -> str:
    # issuer+subject should be unique but let's not leak this info
    username = smart_str(base64.urlsafe_b64encode(hashlib.sha256(force_bytes(issuer + subject)).digest()).rstrip(b"="))
    if User.objects.filter(username=username).exists():
        raise Exception(f"User {username} already exists")
    LOGGER.warning(f"Falling back to username {username} for email {email}")
    return username


def generate_username_with_domain(email: str, issuer: str, subject: str) -> str:
    local_part, domain = utils.split_email_addr(email)
    local_part = utils.sanitize(local_part)
    domain = utils.sanitize(domain.rsplit(".", maxsplit=1)[0])

    if not local_part or not domain:
        return _generate_default_username(email, issuer, subject)
    username = local_part + "-" + domain
    if not User.objects.filter(username=username).exists():
        return username
    return utils.iterate_username(username)


def generate_username(email: str, issuer: str, subject: str) -> str:
    local_part, _ = utils.split_email_addr(email)
    username = utils.sanitize(local_part)

    if not username:
        return _generate_default_username(email, issuer, subject)
    if not User.objects.filter(username=username).exists():
        return username
    return utils.iterate_username(username)
