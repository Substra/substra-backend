from io import BytesIO

from substrapp.compute_tasks.errors import CeleryNoRetryError
from substrapp.compute_tasks.errors import CeleryRetryError
from substrapp.compute_tasks.errors import ComputeTaskErrorType


class PodError(Exception):
    pass


class PodTimeoutError(Exception):
    pass


class _BuildError(RuntimeError):
    """An error occurred during the build of a container image.

    Args:
        logs (str): the container image build logs
    """

    error_type = ComputeTaskErrorType.BUILD_ERROR

    def __init__(self, logs: str, *args: list, **kwargs: dict):
        self.logs = BytesIO(str.encode(logs))
        super().__init__(logs, *args, **kwargs)


class BuildError(_BuildError, CeleryNoRetryError):
    """An error occurred during the build of a container image.

    Args:
        logs (str): the container image build logs
    """


class BuildRetryError(_BuildError, CeleryRetryError):
    """An error occurred during the build of a container image.

    Args:
        logs (str): the container image build logs
    """
