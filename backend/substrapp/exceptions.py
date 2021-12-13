import rest_framework as drf


class ApiError(Exception):
    """Base error response returned by API."""

    status = drf.status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Internal server error."

    def __init__(self, message=None, data=None):
        message = message or self.message

        self.error = data or {}
        self.error["message"] = message

        super().__init__(message)

    def response(self):
        """Get HTTP Response from error instance."""
        return drf.response.Response(self.error, status=self.status)


class BadRequestError(ApiError):
    status = drf.status.HTTP_400_BAD_REQUEST
    message = "Bad request."


class PodError(Exception):
    pass


class PodDeletedError(Exception):
    pass


class PodReadinessTimeoutError(Exception):
    pass


class PodTimeoutError(Exception):
    pass


class NodeError(Exception):
    """An error occurred during the download of an asset from a node"""


class BuildError(Exception):
    """An error occurred during the build of a container image"""


class TaskNotFoundError(Exception):
    """A celery task was not found"""


class ServerMediasNoSubdirError(Exception):
    """A supplied servermedias path didn't contain the expected subdir"""


class AssetPermissionError(Exception):
    def __init__(self, message="Unauthorized"):
        super().__init__(self, message)
