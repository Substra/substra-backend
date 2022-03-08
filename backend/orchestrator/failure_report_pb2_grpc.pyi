"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import failure_report_pb2
import grpc

class FailureReportServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    RegisterFailureReport: grpc.UnaryUnaryMultiCallable[
        failure_report_pb2.NewFailureReport,
        failure_report_pb2.FailureReport]

    GetFailureReport: grpc.UnaryUnaryMultiCallable[
        failure_report_pb2.GetFailureReportParam,
        failure_report_pb2.FailureReport]


class FailureReportServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterFailureReport(self,
        request: failure_report_pb2.NewFailureReport,
        context: grpc.ServicerContext,
    ) -> failure_report_pb2.FailureReport: ...

    @abc.abstractmethod
    def GetFailureReport(self,
        request: failure_report_pb2.GetFailureReportParam,
        context: grpc.ServicerContext,
    ) -> failure_report_pb2.FailureReport: ...


def add_FailureReportServiceServicer_to_server(servicer: FailureReportServiceServicer, server: grpc.Server) -> None: ...
