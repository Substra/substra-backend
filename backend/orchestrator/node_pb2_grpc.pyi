"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import grpc
import node_pb2

class NodeServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    RegisterNode: grpc.UnaryUnaryMultiCallable[
        node_pb2.RegisterNodeParam,
        node_pb2.Node] = ...

    GetAllNodes: grpc.UnaryUnaryMultiCallable[
        node_pb2.GetAllNodesParam,
        node_pb2.GetAllNodesResponse] = ...


class NodeServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterNode(self,
        request: node_pb2.RegisterNodeParam,
        context: grpc.ServicerContext,
    ) -> node_pb2.Node: ...

    @abc.abstractmethod
    def GetAllNodes(self,
        request: node_pb2.GetAllNodesParam,
        context: grpc.ServicerContext,
    ) -> node_pb2.GetAllNodesResponse: ...


def add_NodeServiceServicer_to_server(servicer: NodeServiceServicer, server: grpc.Server) -> None: ...