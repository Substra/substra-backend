from django.conf import settings
from urllib.parse import urlparse


class LocalRequest(object):

    def is_secure(self):
        return not getattr(settings, 'DEBUG')

    def get_host(self):
        # remove protocol (http/https) from default domain
        return urlparse(getattr(settings, 'DEFAULT_DOMAIN')).netloc
