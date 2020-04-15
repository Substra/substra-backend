from django.conf import settings
from statsd import defaults, StatsClient

statsd_enabled = getattr(settings, 'STATSD_ENABLED', False)
statsd_host = getattr(settings, 'STATSD_HOST', defaults.HOST)
statsd_port = getattr(settings, 'STATSD_PORT', defaults.PORT)
statsd_prefix = getattr(settings, 'STATSD_PREFIX', defaults.PREFIX)
statsd_maxudpsize = getattr(settings, 'STATSD_MAXUDPSIZE', defaults.MAXUDPSIZE)
statsd_ipv6 = getattr(settings, 'STATSD_IPV6', defaults.IPV6)


statsd_client = None

if statsd_enabled and statsd_client is None:
    statsd_client = StatsClient(
        host=statsd_host,
        port=statsd_port,
        prefix=statsd_prefix,
        maxudpsize=statsd_maxudpsize,
        ipv6=statsd_ipv6
    )
