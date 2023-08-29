import io

import pytest

from builder import exceptions as build_errors
from orchestrator import failure_report_pb2
from substrapp.compute_tasks import errors


class TestComputeTaskErrorType:
    @pytest.mark.parametrize(
        ("input_value", "expected"),
        [(e.value, e) for e in errors.ComputeTaskErrorType] + [(4, errors.ComputeTaskErrorType.INTERNAL_ERROR)],
    )
    def test_from_int(self, input_value: int, expected: errors.ComputeTaskErrorType):
        result = errors.ComputeTaskErrorType.from_int(input_value)
        assert result == expected


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (build_errors.BuildError(logs="some build error"), failure_report_pb2.ERROR_TYPE_BUILD),
        (errors.ExecutionError(logs=io.BytesIO()), failure_report_pb2.ERROR_TYPE_EXECUTION),
        (Exception(), failure_report_pb2.ERROR_TYPE_INTERNAL),
    ],
)
def test_get_error_type(exc: Exception, expected: str):
    assert errors.get_error_type(exc) == expected
