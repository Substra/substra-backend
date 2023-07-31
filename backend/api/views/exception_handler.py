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
        return response.Response({"message": exc.details}, status=exc.http_status)

    if isinstance(exc, utils.ValidationExceptionError):
        return response.Response({"message": exc.data, "key": exc.key}, status=exc.st)

    if isinstance(exc, ApiError):
        # emits a warning for all requests returning an API error response
        logger.warning("exception", class_name=exc.__class__.__name__, exception=exc)
        return exc.response()

    return rename_detail_to_message(views.exception_handler(exc, context))


def rename_detail_to_message(response):
    """
    rename DRF's "detail" field to "message", to match our own style
    """

    if not hasattr(response, "data") or "detail" not in response.data:
        return response

    if "message" not in response.data:
        response.data["message"] = response.data["detail"]
        del response.data["detail"]
    else:
        # not sure what to do in this case, let's just exchange them
        detail = response.data["message"]
        response.data["message"] = response.data["detail"]
        response.data["detail"] = detail

    return response
