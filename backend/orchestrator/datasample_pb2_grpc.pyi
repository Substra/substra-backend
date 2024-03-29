"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import collections.abc
import datasample_pb2
import grpc
import grpc.aio
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore
    ...

class DataSampleServiceStub:
    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    RegisterDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.RegisterDataSamplesParam,
        datasample_pb2.RegisterDataSamplesResponse,
    ]
    UpdateDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.UpdateDataSamplesParam,
        datasample_pb2.UpdateDataSamplesResponse,
    ]
    QueryDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.QueryDataSamplesParam,
        datasample_pb2.QueryDataSamplesResponse,
    ]
    GetDataSample: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.GetDataSampleParam,
        datasample_pb2.DataSample,
    ]

class DataSampleServiceAsyncStub:
    RegisterDataSamples: grpc.aio.UnaryUnaryMultiCallable[
        datasample_pb2.RegisterDataSamplesParam,
        datasample_pb2.RegisterDataSamplesResponse,
    ]
    UpdateDataSamples: grpc.aio.UnaryUnaryMultiCallable[
        datasample_pb2.UpdateDataSamplesParam,
        datasample_pb2.UpdateDataSamplesResponse,
    ]
    QueryDataSamples: grpc.aio.UnaryUnaryMultiCallable[
        datasample_pb2.QueryDataSamplesParam,
        datasample_pb2.QueryDataSamplesResponse,
    ]
    GetDataSample: grpc.aio.UnaryUnaryMultiCallable[
        datasample_pb2.GetDataSampleParam,
        datasample_pb2.DataSample,
    ]

class DataSampleServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterDataSamples(
        self,
        request: datasample_pb2.RegisterDataSamplesParam,
        context: _ServicerContext,
    ) -> typing.Union[datasample_pb2.RegisterDataSamplesResponse, collections.abc.Awaitable[datasample_pb2.RegisterDataSamplesResponse]]: ...
    @abc.abstractmethod
    def UpdateDataSamples(
        self,
        request: datasample_pb2.UpdateDataSamplesParam,
        context: _ServicerContext,
    ) -> typing.Union[datasample_pb2.UpdateDataSamplesResponse, collections.abc.Awaitable[datasample_pb2.UpdateDataSamplesResponse]]: ...
    @abc.abstractmethod
    def QueryDataSamples(
        self,
        request: datasample_pb2.QueryDataSamplesParam,
        context: _ServicerContext,
    ) -> typing.Union[datasample_pb2.QueryDataSamplesResponse, collections.abc.Awaitable[datasample_pb2.QueryDataSamplesResponse]]: ...
    @abc.abstractmethod
    def GetDataSample(
        self,
        request: datasample_pb2.GetDataSampleParam,
        context: _ServicerContext,
    ) -> typing.Union[datasample_pb2.DataSample, collections.abc.Awaitable[datasample_pb2.DataSample]]: ...

def add_DataSampleServiceServicer_to_server(servicer: DataSampleServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
