"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import dataset_pb2
import grpc

class DatasetServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    GetDataset: grpc.UnaryUnaryMultiCallable[
        dataset_pb2.GetDatasetParam,
        dataset_pb2.Dataset] = ...


class DatasetServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def GetDataset(self,
        request: dataset_pb2.GetDatasetParam,
        context: grpc.ServicerContext,
    ) -> dataset_pb2.Dataset: ...


def add_DatasetServiceServicer_to_server(servicer: DatasetServiceServicer, server: grpc.Server) -> None: ...