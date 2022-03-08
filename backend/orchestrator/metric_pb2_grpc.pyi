"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import grpc
import metric_pb2

class MetricServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    RegisterMetric: grpc.UnaryUnaryMultiCallable[
        metric_pb2.NewMetric,
        metric_pb2.Metric]

    GetMetric: grpc.UnaryUnaryMultiCallable[
        metric_pb2.GetMetricParam,
        metric_pb2.Metric]

    QueryMetrics: grpc.UnaryUnaryMultiCallable[
        metric_pb2.QueryMetricsParam,
        metric_pb2.QueryMetricsResponse]


class MetricServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterMetric(self,
        request: metric_pb2.NewMetric,
        context: grpc.ServicerContext,
    ) -> metric_pb2.Metric: ...

    @abc.abstractmethod
    def GetMetric(self,
        request: metric_pb2.GetMetricParam,
        context: grpc.ServicerContext,
    ) -> metric_pb2.Metric: ...

    @abc.abstractmethod
    def QueryMetrics(self,
        request: metric_pb2.QueryMetricsParam,
        context: grpc.ServicerContext,
    ) -> metric_pb2.QueryMetricsResponse: ...


def add_MetricServiceServicer_to_server(servicer: MetricServiceServicer, server: grpc.Server) -> None: ...
