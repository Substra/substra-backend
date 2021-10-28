import cProfile
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from os import path
from tempfile import gettempdir

import structlog
from django.conf import settings


logger = structlog.get_logger(__name__)


@contextmanager
def profile(filename):
    """
    Profile nested instructions.
    Statistics output in tmpfile prefixed by `filename`.
    WARNING: debug purpose only.

    >>> with profile("query_task"):
    ...     data = client.query_task(params)

    """
    if not settings.DEBUG:
        logger.error("Profile only available in debug mode.")
        yield
        return

    profile = cProfile.Profile()
    profile.enable()
    try:
        yield
    finally:
        profile.disable()
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        filepath = path.join(gettempdir(), f"{filename}_{now}.profile")
        profile.dump_stats(filepath)


def with_profile(filename):
    """
    Profile decorated function.
    Statistics output in tmpfile prefixed by `filename`.
    WARNING: debug purpose only.

    >>> @with_profile("query_task"):
    ... def query_task(params):
    ...     pass

    """
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with profile(filename):
                return function(*args, **kwargs)
        return wrapper
    return decorator
