from django.conf import settings
from django.http import HttpResponse
from substrapp.ledger.connection import get_hfc


class HealthCheckMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/readiness":
                return self.readiness(request)
            elif request.path == "/liveness":
                return self.liveness(request)
        return self.get_response(request)

    def liveness(self, request):
        """
        Returns that the server is alive.
        """
        validate_channels()
        return HttpResponse("OK")

    def readiness(self, request):
        """
        Returns that the server is alive.
        """
        validate_channels()
        return HttpResponse("OK")


def validate_channels():
    # Check ledger connection for each channel
    for channel_name, channel in settings.LEDGER_CHANNELS.items():
        with get_hfc(channel_name) as (loop, client, user):
            # if channel_name starts with 'solo-' channel name is include channel['restricted']
            # get_hfc will throw if the solo channel has more than 1 member
            pass
