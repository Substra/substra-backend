"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import datasample_pb2
import grpc

class DataSampleServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    RegisterDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.RegisterDataSamplesParam,
        datasample_pb2.RegisterDataSamplesResponse]

    UpdateDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.UpdateDataSamplesParam,
        datasample_pb2.UpdateDataSamplesResponse]

    QueryDataSamples: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.QueryDataSamplesParam,
        datasample_pb2.QueryDataSamplesResponse]

    GetDataSample: grpc.UnaryUnaryMultiCallable[
        datasample_pb2.GetDataSampleParam,
        datasample_pb2.DataSample]


class DataSampleServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterDataSamples(self,
        request: datasample_pb2.RegisterDataSamplesParam,
        context: grpc.ServicerContext,
    ) -> datasample_pb2.RegisterDataSamplesResponse: ...

    @abc.abstractmethod
    def UpdateDataSamples(self,
        request: datasample_pb2.UpdateDataSamplesParam,
        context: grpc.ServicerContext,
    ) -> datasample_pb2.UpdateDataSamplesResponse: ...

    @abc.abstractmethod
    def QueryDataSamples(self,
        request: datasample_pb2.QueryDataSamplesParam,
        context: grpc.ServicerContext,
    ) -> datasample_pb2.QueryDataSamplesResponse: ...

    @abc.abstractmethod
    def GetDataSample(self,
        request: datasample_pb2.GetDataSampleParam,
        context: grpc.ServicerContext,
    ) -> datasample_pb2.DataSample: ...


def add_DataSampleServiceServicer_to_server(servicer: DataSampleServiceServicer, server: grpc.Server) -> None: ...
