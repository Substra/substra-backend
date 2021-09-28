from grpc import StatusCode
from rest_framework import status

# Inspired from https://github.com/grpc-ecosystem/grpc-gateway/blob/master/runtime/errors.go#L25-L63
RPC_TO_HTTP = {
    StatusCode.OK: status.HTTP_200_OK,
    StatusCode.CANCELLED: status.HTTP_408_REQUEST_TIMEOUT,
    StatusCode.UNKNOWN: status.HTTP_500_INTERNAL_SERVER_ERROR,
    StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
    StatusCode.DEADLINE_EXCEEDED: status.HTTP_504_GATEWAY_TIMEOUT,
    StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    StatusCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
    StatusCode.RESOURCE_EXHAUSTED: status.HTTP_429_TOO_MANY_REQUESTS,
    StatusCode.FAILED_PRECONDITION: status.HTTP_400_BAD_REQUEST,
    StatusCode.ABORTED: status.HTTP_409_CONFLICT,
    StatusCode.OUT_OF_RANGE: status.HTTP_400_BAD_REQUEST,
    StatusCode.UNIMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
    StatusCode.INTERNAL: status.HTTP_500_INTERNAL_SERVER_ERROR,
    StatusCode.UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    StatusCode.DATA_LOSS: status.HTTP_500_INTERNAL_SERVER_ERROR,
    StatusCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
}


class OrcError(Exception):
    """OrcError may be raised by the orchestrator API layer"""

    def http_status(self):
        """If the error has a gRPC code, returns the matching HTTP code.
        Otherwise, a generic internal server error is returned.
        """
        if self.code:
            return RPC_TO_HTTP.get(self.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return status.HTTP_500_INTERNAL_SERVER_ERROR
