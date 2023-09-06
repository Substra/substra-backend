"""Objects to manage errors occurring in a compute task."""

import enum
from typing import BinaryIO

from orchestrator import failure_report_pb2


class CeleryRetryError(Exception):
    """Inherit from this error if you want Celery to retry on your exception"""

    pass


class CeleryNoRetryError(Exception):
    """Inherit from this error if you don't want Celery to retry on your exception"""

    pass


class ComputeTaskErrorType(enum.Enum):
    """The types of errors that can occur in a compute task.

    Values:
        * BUILD_ERROR: error occurring during the build of the container image.
            Likely to be caused by the user's code.
        * EXECUTION_ERROR: error occurring during the execution of the function/metric container.
            Likely to be caused by the user's code.
        * INTERNAL_ERROR: any other error that does not fall into the previous categories.
            Likely to be caused by a fault in the system. It would require the action of a system
            administrator.

    These types of errors are safe to advertise to the user.
    """

    BUILD_ERROR = failure_report_pb2.ERROR_TYPE_BUILD
    EXECUTION_ERROR = failure_report_pb2.ERROR_TYPE_EXECUTION
    INTERNAL_ERROR = failure_report_pb2.ERROR_TYPE_INTERNAL

    @classmethod
    def from_int(cls, value: int) -> "ComputeTaskErrorType":
        """Convert an int into a `ComputeTaskErrorType`. If the int passed as argument
        does not correspond to an enum element, the value `INTERNAL_ERROR` is returned.

        Args:
            value: The int to parse.

        Returns:
            A `ComputeTaskErrorType` element.
        """
        try:
            return cls(value)
        except ValueError:
            return cls.INTERNAL_ERROR


class _ComputeTaskError(RuntimeError):
    """Base class for the exceptions that can be raised in a compute task to be advertised to the user."""

    error_type: ComputeTaskErrorType


class ExecutionError(_ComputeTaskError, CeleryNoRetryError):
    """An error occurred during the execution of a command in a container image.

    Args:
        logs (BinaryIO): the compute task execution logs
    """

    error_type = ComputeTaskErrorType.EXECUTION_ERROR

    def __init__(self, logs: BinaryIO, *args, **kwargs):
        self.logs = logs
        super().__init__(logs, *args, **kwargs)


def get_error_type(exc: Exception) -> failure_report_pb2.ErrorType:
    """From a given exception, return an error type safe to store and to advertise to the user.

    Args:
        exc: The exception to process.

    Returns:
        The error type corresponding to the exception.
    """

    if isinstance(exc, _ComputeTaskError):
        error_type = exc.error_type
    else:
        error_type = ComputeTaskErrorType.INTERNAL_ERROR

    return error_type.value


class InvalidContextError(_ComputeTaskError, CeleryNoRetryError):
    """Error due to invalid task Context"""

    error_type = ComputeTaskErrorType.INTERNAL_ERROR


class UnsupportedOutputAsset(CeleryNoRetryError):
    """Exception raised when an output asset is of an unsupported kind"""

    pass
