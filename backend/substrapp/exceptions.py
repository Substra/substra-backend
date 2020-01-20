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
    default_status = drf.status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "Internal server error."

    def __init__(self, message=None, data=None, status=None):
        message = message or self.default_message
        status = status or self.default_status

        assert message
        assert status

        self.status = status
        self.error = data or {}
        self.error['message'] = message

        super().__init__(message)

    def response(self):
        """Get HTTP Response from error instance."""
        return drf.response.Response(self.error, status=self.status)


class BadRequestError(_ApiError):
    default_status = drf.status.HTTP_400_BAD_REQUEST
    default_message = "Bad request."


class LedgerError(_ApiError):
    """Forward exception raised from ledger network."""
    default_status = None  # must be set at init
    default_message = None  # must be set at init

    def __init__(self, message, status, data=None):
        super().__init__(message=message, data=data, status=status)


def from_ledger_error(exn, data=None):
    """Returns an API error from a ledger error."""
    # TODO implement better interface between ledger errors and api errors
    message = exn.msg
    data = data or {}
    if hasattr(exn, 'pkhash') and not data.get('key'):
        data['key'] = exn.pkhash
    return LedgerError(f"LedgerError: {message}", exn.status, data=data)
