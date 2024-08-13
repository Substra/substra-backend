import pytest

from substrapp.compute_tasks import errors


class TestComputeTaskErrorType:
    @pytest.mark.parametrize(
        ("input_value", "expected"),
        [(e.value, e) for e in errors.ComputeTaskErrorType] + [(4, errors.ComputeTaskErrorType.INTERNAL_ERROR)],
    )
    def test_from_int(self, input_value: int, expected: errors.ComputeTaskErrorType):
        result = errors.ComputeTaskErrorType.from_int(input_value)
        assert result == expected
