from typing import Optional


class KubernetesError(Exception):
    pass


class PodDeletedError(Exception):
    pass


class PodReadinessTimeoutError(Exception):
    pass


class ImageDeletionError(Exception):
    def __init__(self, image_tag: str, status_code: int = None) -> None:
        message = f"An error happened while deleting the container image. image_tag={image_tag}"
        if status_code:
            message = message + f" status_code={status_code}"
        super().__init__(message)


class OrganizationError(Exception):
    """An error occurred during the download of an asset from a organization"""


class OrganizationHttpError(OrganizationError):
    """An error occurred during the request to an organization"""

    def __init__(self, url: str, status_code: Optional[int] = None):
        self.url = url
        self.status_code = status_code
        super().__init__(f"URL: {url} returned status code {status_code or 'unknown'}")


class IntegrityError(Exception):
    """An asset downloaded from a organization has an invalid checksum"""


class ServerMediasNoSubdirError(Exception):
    """A supplied servermedias path didn't contain the expected subdir"""
