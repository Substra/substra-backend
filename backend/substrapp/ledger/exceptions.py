from rest_framework import status


def raise_for_status(response):
    """Parse ledger response and raise exceptions in case of errors."""
    if not response or 'error' not in response:
        return

    if 'cannot change status' in response['error']:
        raise LedgerStatusError.from_response_dict(response)

    status_code = response['status']
    exception_class = _STATUS_TO_EXCEPTION.get(status_code, LedgerError)

    raise exception_class.from_response_dict(response)


class LedgerError(Exception):
    """Base error from ledger."""
    # FIXME the base error status code should be 500, the chaincode is currently
    #       responding with 500 status code for some 400 errors
    status = status.HTTP_400_BAD_REQUEST  # status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    @classmethod
    def from_response_dict(cls, response):
        return cls(response['error'])


class LedgerStatusError(LedgerError):
    """Could not update tuple status error."""
    pass


class LedgerInvalidResponse(LedgerError):
    """Could not parse ledger response."""
    pass


class LedgerTimeout(LedgerError):
    """Ledger does not respond in time."""
    status = status.HTTP_408_REQUEST_TIMEOUT


class LedgerMVCCError(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerPhantomReadConflictError(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerEndorsementPolicyFailure(LedgerError):
    status = status.HTTP_412_PRECONDITION_FAILED


class LedgerUnavailable(LedgerError):
    """Ledger is not available."""
    status = status.HTTP_503_SERVICE_UNAVAILABLE


class LedgerBadRequest(LedgerError):
    """Invalid request."""
    status = status.HTTP_400_BAD_REQUEST


class LedgerConflict(LedgerError):
    """Asset already exists."""
    status = status.HTTP_409_CONFLICT

    def __init__(self, msg, key):
        super().__init__(msg)
        self.key = key

    @classmethod
    def from_response_dict(cls, response):
        key = response.get('key')
        if not key:
            return LedgerError(response['error'])
        return cls(response['error'], key=key)


class LedgerAssetNotFound(LedgerError):
    """Asset not found."""
    status = status.HTTP_404_NOT_FOUND


class LedgerForbidden(LedgerError):
    """Organisation is not allowed to perform the operation."""
    status = status.HTTP_403_FORBIDDEN


_STATUS_TO_EXCEPTION = {
    status.HTTP_400_BAD_REQUEST: LedgerBadRequest,
    status.HTTP_403_FORBIDDEN: LedgerForbidden,
    status.HTTP_404_NOT_FOUND: LedgerAssetNotFound,
    status.HTTP_409_CONFLICT: LedgerConflict,
}
