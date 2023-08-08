from rest_framework import response
from rest_framework import status


class AlreadyExistsError(Exception):
    """The asset was already created in the local representation"""

    pass


class ApiError(Exception):
    """Base error response returned by API."""

    status = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error."

    def __init__(self, detail=None, data=None):
        detail = detail or self.detail

        self.error = data or {}
        self.error["detail"] = detail

        super().__init__(detail)

    def response(self):
        """Get HTTP Response from error instance."""
        return response.Response(self.error, status=self.status)


class BadRequestError(ApiError):
    status = status.HTTP_400_BAD_REQUEST
    detail = "Bad request."


class AssetPermissionError(Exception):
    def __init__(self, detail="Unauthorized"):
        super().__init__(self, detail)
