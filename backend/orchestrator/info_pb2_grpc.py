# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import info_pb2 as info__pb2


class InfoServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.QueryVersion = channel.unary_unary(
                '/orchestrator.InfoService/QueryVersion',
                request_serializer=info__pb2.QueryVersionParam.SerializeToString,
                response_deserializer=info__pb2.QueryVersionResponse.FromString,
                )


class InfoServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def QueryVersion(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_InfoServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'QueryVersion': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryVersion,
                    request_deserializer=info__pb2.QueryVersionParam.FromString,
                    response_serializer=info__pb2.QueryVersionResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'orchestrator.InfoService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class InfoService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def QueryVersion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.InfoService/QueryVersion',
            info__pb2.QueryVersionParam.SerializeToString,
            info__pb2.QueryVersionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
