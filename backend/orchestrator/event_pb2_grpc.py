# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import event_pb2 as event__pb2


class EventServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.QueryEvents = channel.unary_unary(
                '/orchestrator.EventService/QueryEvents',
                request_serializer=event__pb2.QueryEventsParam.SerializeToString,
                response_deserializer=event__pb2.QueryEventsResponse.FromString,
                )
        self.SubscribeToEvents = channel.unary_stream(
                '/orchestrator.EventService/SubscribeToEvents',
                request_serializer=event__pb2.SubscribeToEventsParam.SerializeToString,
                response_deserializer=event__pb2.Event.FromString,
                )


class EventServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def QueryEvents(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubscribeToEvents(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_EventServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'QueryEvents': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryEvents,
                    request_deserializer=event__pb2.QueryEventsParam.FromString,
                    response_serializer=event__pb2.QueryEventsResponse.SerializeToString,
            ),
            'SubscribeToEvents': grpc.unary_stream_rpc_method_handler(
                    servicer.SubscribeToEvents,
                    request_deserializer=event__pb2.SubscribeToEventsParam.FromString,
                    response_serializer=event__pb2.Event.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'orchestrator.EventService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class EventService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def QueryEvents(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.EventService/QueryEvents',
            event__pb2.QueryEventsParam.SerializeToString,
            event__pb2.QueryEventsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SubscribeToEvents(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/orchestrator.EventService/SubscribeToEvents',
            event__pb2.SubscribeToEventsParam.SerializeToString,
            event__pb2.Event.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
