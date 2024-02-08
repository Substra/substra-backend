"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import collections.abc
import function_pb2
import grpc
import grpc.aio
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore
    ...

class FunctionServiceStub:
    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    RegisterFunction: grpc.UnaryUnaryMultiCallable[
        function_pb2.NewFunction,
        function_pb2.Function,
    ]
    GetFunction: grpc.UnaryUnaryMultiCallable[
        function_pb2.GetFunctionParam,
        function_pb2.Function,
    ]
    QueryFunctions: grpc.UnaryUnaryMultiCallable[
        function_pb2.QueryFunctionsParam,
        function_pb2.QueryFunctionsResponse,
    ]
    UpdateFunction: grpc.UnaryUnaryMultiCallable[
        function_pb2.UpdateFunctionParam,
        function_pb2.UpdateFunctionResponse,
    ]
    ApplyFunctionAction: grpc.UnaryUnaryMultiCallable[
        function_pb2.ApplyFunctionActionParam,
        function_pb2.ApplyFunctionActionResponse,
    ]

class FunctionServiceAsyncStub:
    RegisterFunction: grpc.aio.UnaryUnaryMultiCallable[
        function_pb2.NewFunction,
        function_pb2.Function,
    ]
    GetFunction: grpc.aio.UnaryUnaryMultiCallable[
        function_pb2.GetFunctionParam,
        function_pb2.Function,
    ]
    QueryFunctions: grpc.aio.UnaryUnaryMultiCallable[
        function_pb2.QueryFunctionsParam,
        function_pb2.QueryFunctionsResponse,
    ]
    UpdateFunction: grpc.aio.UnaryUnaryMultiCallable[
        function_pb2.UpdateFunctionParam,
        function_pb2.UpdateFunctionResponse,
    ]
    ApplyFunctionAction: grpc.aio.UnaryUnaryMultiCallable[
        function_pb2.ApplyFunctionActionParam,
        function_pb2.ApplyFunctionActionResponse,
    ]

class FunctionServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterFunction(
        self,
        request: function_pb2.NewFunction,
        context: _ServicerContext,
    ) -> typing.Union[function_pb2.Function, collections.abc.Awaitable[function_pb2.Function]]: ...
    @abc.abstractmethod
    def GetFunction(
        self,
        request: function_pb2.GetFunctionParam,
        context: _ServicerContext,
    ) -> typing.Union[function_pb2.Function, collections.abc.Awaitable[function_pb2.Function]]: ...
    @abc.abstractmethod
    def QueryFunctions(
        self,
        request: function_pb2.QueryFunctionsParam,
        context: _ServicerContext,
    ) -> typing.Union[function_pb2.QueryFunctionsResponse, collections.abc.Awaitable[function_pb2.QueryFunctionsResponse]]: ...
    @abc.abstractmethod
    def UpdateFunction(
        self,
        request: function_pb2.UpdateFunctionParam,
        context: _ServicerContext,
    ) -> typing.Union[function_pb2.UpdateFunctionResponse, collections.abc.Awaitable[function_pb2.UpdateFunctionResponse]]: ...
    @abc.abstractmethod
    def ApplyFunctionAction(
        self,
        request: function_pb2.ApplyFunctionActionParam,
        context: _ServicerContext,
    ) -> typing.Union[function_pb2.ApplyFunctionActionResponse, collections.abc.Awaitable[function_pb2.ApplyFunctionActionResponse]]: ...

def add_FunctionServiceServicer_to_server(servicer: FunctionServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
