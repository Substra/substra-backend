import unittest

from parameterized import parameterized

from substrapp.compute_tasks import errors


class TestComputeTaskErrors(unittest.TestCase):
    @parameterized.expand(
        [
            (errors.BuildError, "BUILD_ERROR"),
            (errors.ExecutionError, "EXECUTION_ERROR"),
            (Exception, "INTERNAL_ERROR"),
        ]
    )
    def test_get_error_type(self, exc_class, expected):
        self.assertEqual(errors.get_error_type(exc_class()), expected)
