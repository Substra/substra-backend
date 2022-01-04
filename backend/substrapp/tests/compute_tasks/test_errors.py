import io

import pytest

from substrapp.compute_tasks import errors


class TestComputeTaskErrorType:
    @pytest.mark.parametrize(
        ("input_value", "expected"),
        [(e.name, e) for e in errors.ComputeTaskErrorType]
        + [("Some unexpected internal error", errors.ComputeTaskErrorType.INTERNAL_ERROR)],
    )
    def test_from_str(self, input_value: str, expected: errors.ComputeTaskErrorType):
        result = errors.ComputeTaskErrorType.from_str(input_value)
        assert result == expected


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (errors.BuildError(), "BUILD_ERROR"),
        (errors.ExecutionError(logs=io.BytesIO()), "EXECUTION_ERROR"),
        (Exception(), "INTERNAL_ERROR"),
    ],
)
def test_get_error_type(exc: Exception, expected: str):
    assert errors.get_error_type(exc) == expected
