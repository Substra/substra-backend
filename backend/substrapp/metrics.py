from django.conf import settings
from statsd import defaults, StatsClient
from functools import wraps


class NullStatsClient(StatsClient):
    def timing(self, *args, **kwargs):
        pass

    def incr(self, *args, **kwargs):
        pass

    def decr(self, *args, **kwargs):
        pass

    def gauge(self, *args, **kwargs):
        pass

    def set(self, *args, **kwargs):
        pass

    def timer(self, *args, **kwargs):
        def passthrough(f):
            @wraps(f)
            def _wrapped(*fargs, **fkwargs):
                return f(*fargs, **fkwargs)

            return _wrapped
        return passthrough


_statsd_client = None


def initialize():
    global _statsd_client

    if settings.STATSD_ENABLED:
        statsd_host = getattr(settings, 'STATSD_HOST', defaults.HOST)
        statsd_port = getattr(settings, 'STATSD_PORT', defaults.PORT)
        statsd_prefix = getattr(settings, 'STATSD_PREFIX', defaults.PREFIX)
        statsd_maxudpsize = getattr(settings, 'STATSD_MAXUDPSIZE', defaults.MAXUDPSIZE)
        statsd_ipv6 = getattr(settings, 'STATSD_IPV6', defaults.IPV6)

        _statsd_client = StatsClient(
            host=statsd_host,
            port=statsd_port,
            prefix=statsd_prefix,
            maxudpsize=statsd_maxudpsize,
            ipv6=statsd_ipv6
        )
    else:
        _statsd_client = NullStatsClient()

    return _statsd_client


def get_metrics_client():
    if not _statsd_client:
        initialize()

    return _statsd_client
