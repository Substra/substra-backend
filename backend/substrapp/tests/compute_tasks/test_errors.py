import unittest
from typing import Type

from parameterized import parameterized

from substrapp.compute_tasks import errors


class TestComputeTaskErrorType(unittest.TestCase):
    @parameterized.expand(
        [(e.name, e) for e in errors.ComputeTaskErrorType]
        + [("Some unexpected internal error", errors.ComputeTaskErrorType.INTERNAL_ERROR)]
    )
    def test_from_str(self, input_value: str, expected: errors.ComputeTaskErrorType):
        result = errors.ComputeTaskErrorType.from_str(input_value)
        self.assertEqual(result, expected)


class TestComputeTaskErrors(unittest.TestCase):
    @parameterized.expand(
        [
            (errors.BuildError, "BUILD_ERROR"),
            (errors.ExecutionError, "EXECUTION_ERROR"),
            (Exception, "INTERNAL_ERROR"),
        ]
    )
    def test_get_error_type(self, exc_class: Type[Exception], expected: str):
        self.assertEqual(errors.get_error_type(exc_class()), expected)
