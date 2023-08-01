import structlog
from rest_framework import response
from rest_framework import views

import orchestrator.error
from api.errors import ApiError
from api.views import utils

logger = structlog.get_logger(__name__)


def api_exception_handler(exc, context):
    """API Exception handler."""
    if isinstance(exc, orchestrator.error.OrcError):
        return response.Response({"detail": exc.details}, status=exc.http_status)

    if isinstance(exc, utils.ValidationExceptionError):
        return response.Response({"detail": exc.data, "key": exc.key}, status=exc.st)

    if isinstance(exc, ApiError):
        # emits a warning for all requests returning an API error response
        logger.warning("exception", class_name=exc.__class__.__name__, exception=exc)
        return exc.response()

    return views.exception_handler(exc, context)
