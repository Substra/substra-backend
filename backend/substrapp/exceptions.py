from rest_framework import response
from rest_framework import status


class ApiError(Exception):
    """Base error response returned by API."""

    status = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Internal server error."

    def __init__(self, message=None, data=None):
        message = message or self.message

        self.error = data or {}
        self.error["message"] = message

        super().__init__(message)

    def response(self):
        """Get HTTP Response from error instance."""
        return response.Response(self.error, status=self.status)


class BadRequestError(ApiError):
    status = status.HTTP_400_BAD_REQUEST
    message = "Bad request."


class KubernetesError(Exception):
    pass


class PodError(Exception):
    pass


class PodDeletedError(Exception):
    pass


class PodReadinessTimeoutError(Exception):
    pass


class PodTimeoutError(Exception):
    pass


class ImageDeletionError(Exception):
    def __init__(self, image_tag: str, status_code: int = None) -> None:
        message = f"An error happened while deleting the container image. image_tag={image_tag}"
        if status_code:
            message = message + f" status_code={status_code}"
        super().__init__(message)


class OrganizationError(Exception):
    """An error occurred during the download of an asset from a organization"""


class IntegrityError(Exception):
    """An asset downloaded from a organization has an invalid checksum"""


class ServerMediasNoSubdirError(Exception):
    """A supplied servermedias path didn't contain the expected subdir"""


class AssetPermissionError(Exception):
    def __init__(self, message="Unauthorized"):
        super().__init__(self, message)
