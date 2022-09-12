import unittest

import grpc
from rest_framework import status

import orchestrator.error
from api.views import exception_handler
from api.views import utils


class ApiExceptionHandlerTests(unittest.TestCase):
    def test_catch_orchestrator_error(self):
        details, code = "out of range test", grpc.StatusCode.OUT_OF_RANGE
        exc = orchestrator.error.OrcError()
        exc.details = details
        exc.code = code
        response = exception_handler.api_exception_handler(exc, None)

        self.assertEqual(response.status_code, orchestrator.error.RPC_TO_HTTP[code])
        self.assertEqual(response.data["message"], details)

    def test_catch_custom_validation_error(self):
        message, key, status_code = "foo", "bar", status.HTTP_403_FORBIDDEN
        exc = utils.ValidationExceptionError(message, key, status_code)
        response = exception_handler.api_exception_handler(exc, None)

        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.data["message"], message)
        self.assertEqual(response.data["key"], key)
