# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from . import profiling_pb2 as profiling__pb2


class ProfilingServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterProfilingStep = channel.unary_unary(
                '/orchestrator.ProfilingService/RegisterProfilingStep',
                request_serializer=profiling__pb2.ProfilingStep.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class ProfilingServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterProfilingStep(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ProfilingServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterProfilingStep': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterProfilingStep,
                    request_deserializer=profiling__pb2.ProfilingStep.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'orchestrator.ProfilingService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ProfilingService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterProfilingStep(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ProfilingService/RegisterProfilingStep',
            profiling__pb2.ProfilingStep.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
