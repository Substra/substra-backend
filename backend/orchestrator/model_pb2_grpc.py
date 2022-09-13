# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import model_pb2 as model__pb2


class ModelServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterModel = channel.unary_unary(
                '/orchestrator.ModelService/RegisterModel',
                request_serializer=model__pb2.NewModel.SerializeToString,
                response_deserializer=model__pb2.Model.FromString,
                )
        self.RegisterModels = channel.unary_unary(
                '/orchestrator.ModelService/RegisterModels',
                request_serializer=model__pb2.RegisterModelsParam.SerializeToString,
                response_deserializer=model__pb2.RegisterModelsResponse.FromString,
                )
        self.GetModel = channel.unary_unary(
                '/orchestrator.ModelService/GetModel',
                request_serializer=model__pb2.GetModelParam.SerializeToString,
                response_deserializer=model__pb2.Model.FromString,
                )
        self.GetComputeTaskOutputModels = channel.unary_unary(
                '/orchestrator.ModelService/GetComputeTaskOutputModels',
                request_serializer=model__pb2.GetComputeTaskModelsParam.SerializeToString,
                response_deserializer=model__pb2.GetComputeTaskModelsResponse.FromString,
                )
        self.CanDisableModel = channel.unary_unary(
                '/orchestrator.ModelService/CanDisableModel',
                request_serializer=model__pb2.CanDisableModelParam.SerializeToString,
                response_deserializer=model__pb2.CanDisableModelResponse.FromString,
                )
        self.DisableModel = channel.unary_unary(
                '/orchestrator.ModelService/DisableModel',
                request_serializer=model__pb2.DisableModelParam.SerializeToString,
                response_deserializer=model__pb2.DisableModelResponse.FromString,
                )


class ModelServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterModel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RegisterModels(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetModel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetComputeTaskOutputModels(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CanDisableModel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DisableModel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ModelServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterModel': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterModel,
                    request_deserializer=model__pb2.NewModel.FromString,
                    response_serializer=model__pb2.Model.SerializeToString,
            ),
            'RegisterModels': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterModels,
                    request_deserializer=model__pb2.RegisterModelsParam.FromString,
                    response_serializer=model__pb2.RegisterModelsResponse.SerializeToString,
            ),
            'GetModel': grpc.unary_unary_rpc_method_handler(
                    servicer.GetModel,
                    request_deserializer=model__pb2.GetModelParam.FromString,
                    response_serializer=model__pb2.Model.SerializeToString,
            ),
            'GetComputeTaskOutputModels': grpc.unary_unary_rpc_method_handler(
                    servicer.GetComputeTaskOutputModels,
                    request_deserializer=model__pb2.GetComputeTaskModelsParam.FromString,
                    response_serializer=model__pb2.GetComputeTaskModelsResponse.SerializeToString,
            ),
            'CanDisableModel': grpc.unary_unary_rpc_method_handler(
                    servicer.CanDisableModel,
                    request_deserializer=model__pb2.CanDisableModelParam.FromString,
                    response_serializer=model__pb2.CanDisableModelResponse.SerializeToString,
            ),
            'DisableModel': grpc.unary_unary_rpc_method_handler(
                    servicer.DisableModel,
                    request_deserializer=model__pb2.DisableModelParam.FromString,
                    response_serializer=model__pb2.DisableModelResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'orchestrator.ModelService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ModelService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterModel(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/RegisterModel',
            model__pb2.NewModel.SerializeToString,
            model__pb2.Model.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RegisterModels(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/RegisterModels',
            model__pb2.RegisterModelsParam.SerializeToString,
            model__pb2.RegisterModelsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetModel(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/GetModel',
            model__pb2.GetModelParam.SerializeToString,
            model__pb2.Model.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetComputeTaskOutputModels(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/GetComputeTaskOutputModels',
            model__pb2.GetComputeTaskModelsParam.SerializeToString,
            model__pb2.GetComputeTaskModelsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CanDisableModel(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/CanDisableModel',
            model__pb2.CanDisableModelParam.SerializeToString,
            model__pb2.CanDisableModelResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DisableModel(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/orchestrator.ModelService/DisableModel',
            model__pb2.DisableModelParam.SerializeToString,
            model__pb2.DisableModelResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
