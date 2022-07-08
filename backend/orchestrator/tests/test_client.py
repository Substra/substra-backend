import grpc

from orchestrator.client import GRPC_RETRYABLE_ERRORS
from orchestrator.client import grpc_retry
from orchestrator.error import OrcError


class FakeClient:
    @grpc_retry
    def fun(self, foo, bar):
        # ensure args have not been modified
        assert foo["key"] == "value"
        assert bar["key"] == "value"

        # mutate args
        foo["key"] = "modified value"
        bar["key"] = "modified value"

        # ensure the function is retried by the decorator @grpc_retry
        ex = grpc.RpcError()
        ex.code = lambda: GRPC_RETRYABLE_ERRORS[0]
        ex.details = lambda: "fake rcp error"
        raise ex


def test_grpc_retry():
    try:
        # The function fun should be retried several times, but it should always receive the same *args and **kwargs
        FakeClient().fun({"key": "value"}, bar={"key": "value"})
    except OrcError:
        pass  # expected
