"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import collections.abc
import grpc
import grpc.aio
import organization_pb2
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore
    ...

class OrganizationServiceStub:
    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    RegisterOrganization: grpc.UnaryUnaryMultiCallable[
        organization_pb2.RegisterOrganizationParam,
        organization_pb2.Organization,
    ]
    GetAllOrganizations: grpc.UnaryUnaryMultiCallable[
        organization_pb2.GetAllOrganizationsParam,
        organization_pb2.GetAllOrganizationsResponse,
    ]

class OrganizationServiceAsyncStub:
    RegisterOrganization: grpc.aio.UnaryUnaryMultiCallable[
        organization_pb2.RegisterOrganizationParam,
        organization_pb2.Organization,
    ]
    GetAllOrganizations: grpc.aio.UnaryUnaryMultiCallable[
        organization_pb2.GetAllOrganizationsParam,
        organization_pb2.GetAllOrganizationsResponse,
    ]

class OrganizationServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def RegisterOrganization(
        self,
        request: organization_pb2.RegisterOrganizationParam,
        context: _ServicerContext,
    ) -> typing.Union[organization_pb2.Organization, collections.abc.Awaitable[organization_pb2.Organization]]: ...
    @abc.abstractmethod
    def GetAllOrganizations(
        self,
        request: organization_pb2.GetAllOrganizationsParam,
        context: _ServicerContext,
    ) -> typing.Union[organization_pb2.GetAllOrganizationsResponse, collections.abc.Awaitable[organization_pb2.GetAllOrganizationsResponse]]: ...

def add_OrganizationServiceServicer_to_server(servicer: OrganizationServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
