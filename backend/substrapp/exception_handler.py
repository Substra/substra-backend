import rest_framework as drf
import structlog

import orchestrator.error
from substrapp import exceptions
from substrapp.views import utils

logger = structlog.get_logger(__name__)


def api_exception_handler(exc, context):
    """API Exception handler."""
    if isinstance(exc, orchestrator.error.OrcError):
        return drf.response.Response({"message": exc.details}, status=exc.http_status())

    if isinstance(exc, utils.ValidationExceptionError):
        return drf.response.Response({"message": exc.data, "key": exc.key}, status=exc.st)

    if isinstance(exc, exceptions.ApiError):
        # emits a warning for all requests returning an API error response
        logger.warning("exception", class_name=exc.__class__.__name__, exception=exc)
        return exc.response()

    return drf.views.exception_handler(exc, context)
