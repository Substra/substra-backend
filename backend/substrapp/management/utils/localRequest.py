from django.conf import settings


class LocalRequest(object):

    def is_secure(self):
        return not getattr(settings, 'DEBUG')

    def get_host(self):
        # remove protocol (http/https) from default domain
        return getattr(settings, 'DEFAULT_DOMAIN').split('//')[-1]
