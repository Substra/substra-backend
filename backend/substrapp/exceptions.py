import logging

import rest_framework as drf

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """API Exception handler."""
    if isinstance(exc, _ApiError):
        # emits a warning for all requests returning an API error response
        logger.warning(f"{exc.__class__.__name__}: {exc}")
        response = exc.response()
    else:
        response = drf.views.exception_handler(exc, context)
    return response


class _ApiError(Exception):
    """Base error response returned by API."""
    status = drf.status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Internal server error."

    def __init__(self, message=None, data=None):
        message = message or self.message

        self.error = data or {}
        self.error['message'] = message

        super().__init__(message)

    def response(self):
        """Get HTTP Response from error instance."""
        return drf.response.Response(self.error, status=self.status)


class BadRequestError(_ApiError):
    status = drf.status.HTTP_400_BAD_REQUEST
    message = "Bad request."
