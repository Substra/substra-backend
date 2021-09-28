from django.conf import settings
from django.http import HttpResponse
from substrapp.orchestrator import get_orchestrator_client


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
    # Check orchetrator connection for each channel
    for channel_name, channel_settings in settings.LEDGER_CHANNELS.items():
        with get_orchestrator_client(channel_name) as client:
            # throw an Execption if the solo channel has more than 1 member
            if channel_name.startswith('solo-') or channel_settings['restricted']:
                nodes = [node['id'] for node in client.query_nodes()]
                if (len(nodes) > 1):
                    raise Exception(f'Restricted channel {channel_name} should have at most 1 member, but has '
                                    f'{len(nodes)}')
