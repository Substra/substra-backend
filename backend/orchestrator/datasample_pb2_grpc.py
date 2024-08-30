# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from . import datasample_pb2 as datasample__pb2

GRPC_GENERATED_VERSION = '1.66.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in datasample_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class DataSampleServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterDataSamples = channel.unary_unary(
                '/orchestrator.DataSampleService/RegisterDataSamples',
                request_serializer=datasample__pb2.RegisterDataSamplesParam.SerializeToString,
                response_deserializer=datasample__pb2.RegisterDataSamplesResponse.FromString,
                _registered_method=True)
        self.UpdateDataSamples = channel.unary_unary(
                '/orchestrator.DataSampleService/UpdateDataSamples',
                request_serializer=datasample__pb2.UpdateDataSamplesParam.SerializeToString,
                response_deserializer=datasample__pb2.UpdateDataSamplesResponse.FromString,
                _registered_method=True)
        self.QueryDataSamples = channel.unary_unary(
                '/orchestrator.DataSampleService/QueryDataSamples',
                request_serializer=datasample__pb2.QueryDataSamplesParam.SerializeToString,
                response_deserializer=datasample__pb2.QueryDataSamplesResponse.FromString,
                _registered_method=True)
        self.GetDataSample = channel.unary_unary(
                '/orchestrator.DataSampleService/GetDataSample',
                request_serializer=datasample__pb2.GetDataSampleParam.SerializeToString,
                response_deserializer=datasample__pb2.DataSample.FromString,
                _registered_method=True)


class DataSampleServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterDataSamples(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateDataSamples(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueryDataSamples(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDataSample(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DataSampleServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterDataSamples': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterDataSamples,
                    request_deserializer=datasample__pb2.RegisterDataSamplesParam.FromString,
                    response_serializer=datasample__pb2.RegisterDataSamplesResponse.SerializeToString,
            ),
            'UpdateDataSamples': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateDataSamples,
                    request_deserializer=datasample__pb2.UpdateDataSamplesParam.FromString,
                    response_serializer=datasample__pb2.UpdateDataSamplesResponse.SerializeToString,
            ),
            'QueryDataSamples': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryDataSamples,
                    request_deserializer=datasample__pb2.QueryDataSamplesParam.FromString,
                    response_serializer=datasample__pb2.QueryDataSamplesResponse.SerializeToString,
            ),
            'GetDataSample': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDataSample,
                    request_deserializer=datasample__pb2.GetDataSampleParam.FromString,
                    response_serializer=datasample__pb2.DataSample.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'orchestrator.DataSampleService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('orchestrator.DataSampleService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class DataSampleService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterDataSamples(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/orchestrator.DataSampleService/RegisterDataSamples',
            datasample__pb2.RegisterDataSamplesParam.SerializeToString,
            datasample__pb2.RegisterDataSamplesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateDataSamples(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/orchestrator.DataSampleService/UpdateDataSamples',
            datasample__pb2.UpdateDataSamplesParam.SerializeToString,
            datasample__pb2.UpdateDataSamplesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueryDataSamples(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/orchestrator.DataSampleService/QueryDataSamples',
            datasample__pb2.QueryDataSamplesParam.SerializeToString,
            datasample__pb2.QueryDataSamplesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetDataSample(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/orchestrator.DataSampleService/GetDataSample',
            datasample__pb2.GetDataSampleParam.SerializeToString,
            datasample__pb2.DataSample.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
