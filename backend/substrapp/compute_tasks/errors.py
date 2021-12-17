"""Objects to manage errors occurring in a compute task."""

import abc
import enum


class ComputeTaskErrorType(enum.Enum):
    """The types of errors that can occur in a compute task.

    Values:
        * BUILD_ERROR: error occurring during the build of the container image.
            Likely to be caused by the user's code.
        * EXECUTION_ERROR: error occurring during the execution of the algo/metric container.
            Likely to be caused by the user's code.
        * INTERNAL_ERROR: any other error that does not fall into the previous categories.
            Likely to be caused by a fault in the system. It would require the action of a system
            administrator.

    These types of errors are safe to advertise to the user.
    """

    def _generate_next_value_(name, start, count, last_values):  # noqa: N805
        return name

    BUILD_ERROR = enum.auto()
    EXECUTION_ERROR = enum.auto()
    INTERNAL_ERROR = enum.auto()

    @classmethod
    def from_str(cls, value: str) -> "ComputeTaskErrorType":
        """Convert a string into a `ComputeTaskErrorType`. If the string passed as argument
        does not correspond to an enum element, the value `INTERNAL_ERROR` is returned.

        Args:
            value: The string to parse.

        Returns:
            A `ComputeTaskErrorType` element.
        """
        try:
            return cls(value)
        except ValueError:
            return cls.INTERNAL_ERROR


class _ComputeTaskError(RuntimeError, abc.ABC):
    """Base class for the exceptions that can be raised in a compute task to be advertised to the user."""

    error_type: ComputeTaskErrorType


class BuildError(_ComputeTaskError):
    """An error occurred during the build of a container image."""

    error_type = ComputeTaskErrorType.BUILD_ERROR


class ExecutionError(_ComputeTaskError):
    """An error occurred during the execution of a command in a container image."""

    error_type = ComputeTaskErrorType.EXECUTION_ERROR


def get_error_type(exc: Exception) -> str:
    """From a given exception, return an error type safe to store and to advertise to the user.

    Args:
        exc: The exception to process.

    Returns:
        The error code corresponding to the exception, as a string.
    """

    if isinstance(exc, _ComputeTaskError):
        return exc.error_type.value

    return ComputeTaskErrorType.INTERNAL_ERROR.value
