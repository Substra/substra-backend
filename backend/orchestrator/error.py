from typing import Optional

from grpc import StatusCode
from rest_framework import status

# Mappings taken from https://github.com/grpc-ecosystem/grpc-gateway/blob/cb1fb905323b977e0ebb77a890696d7e30c9bc96/runtime/errors.go#L34-L77  # noqa: E501
RPC_TO_HTTP = {
    StatusCode.OK: status.HTTP_200_OK,
    StatusCode.CANCELLED: status.HTTP_408_REQUEST_TIMEOUT,
    StatusCode.UNKNOWN: status.HTTP_500_INTERNAL_SERVER_ERROR,
    StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
    StatusCode.DEADLINE_EXCEEDED: status.HTTP_504_GATEWAY_TIMEOUT,
    StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    StatusCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
    StatusCode.RESOURCE_EXHAUSTED: status.HTTP_429_TOO_MANY_REQUESTS,  # may be translated to HTTP_413_REQUEST_ENTITY_TOO_LARGE instead, see below  # noqa: E501
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

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.details = ""
        self.code: Optional[StatusCode] = None

    @property
    def http_status(self):
        """If the error has a gRPC code, returns the matching HTTP code.
        Otherwise, a generic internal server error is returned.
        """
        if self.code:
            if "message larger than max" in str(self) and self.code == StatusCode.RESOURCE_EXHAUSTED:
                return status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            elif self.code in RPC_TO_HTTP:
                return RPC_TO_HTTP[self.code]

        return status.HTTP_500_INTERNAL_SERVER_ERROR
