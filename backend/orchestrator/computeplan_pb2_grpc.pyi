"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import computeplan_pb2
import grpc

class ComputePlanServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    RegisterPlan: grpc.UnaryUnaryMultiCallable[
        computeplan_pb2.NewComputePlan,
        computeplan_pb2.ComputePlan]

    GetPlan: grpc.UnaryUnaryMultiCallable[
        computeplan_pb2.GetComputePlanParam,
        computeplan_pb2.ComputePlan]

    ApplyPlanAction: grpc.UnaryUnaryMultiCallable[
        computeplan_pb2.ApplyPlanActionParam,
        computeplan_pb2.ApplyPlanActionResponse]

    QueryPlans: grpc.UnaryUnaryMultiCallable[
        computeplan_pb2.QueryPlansParam,
        computeplan_pb2.QueryPlansResponse]


class ComputePlanServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterPlan(self,
        request: computeplan_pb2.NewComputePlan,
        context: grpc.ServicerContext,
    ) -> computeplan_pb2.ComputePlan: ...

    @abc.abstractmethod
    def GetPlan(self,
        request: computeplan_pb2.GetComputePlanParam,
        context: grpc.ServicerContext,
    ) -> computeplan_pb2.ComputePlan: ...

    @abc.abstractmethod
    def ApplyPlanAction(self,
        request: computeplan_pb2.ApplyPlanActionParam,
        context: grpc.ServicerContext,
    ) -> computeplan_pb2.ApplyPlanActionResponse: ...

    @abc.abstractmethod
    def QueryPlans(self,
        request: computeplan_pb2.QueryPlansParam,
        context: grpc.ServicerContext,
    ) -> computeplan_pb2.QueryPlansResponse: ...


def add_ComputePlanServiceServicer_to_server(servicer: ComputePlanServiceServicer, server: grpc.Server) -> None: ...
