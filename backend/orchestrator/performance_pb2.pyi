"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.timestamp_pb2
import typing
import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor = ...

class NewPerformance(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    METRIC_KEY_FIELD_NUMBER: builtins.int
    PERFORMANCE_VALUE_FIELD_NUMBER: builtins.int
    compute_task_key: typing.Text = ...
    metric_key: typing.Text = ...
    performance_value: builtins.float = ...
    def __init__(self,
        *,
        compute_task_key : typing.Text = ...,
        metric_key : typing.Text = ...,
        performance_value : builtins.float = ...,
        ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_task_key",b"compute_task_key","metric_key",b"metric_key","performance_value",b"performance_value"]) -> None: ...
global___NewPerformance = NewPerformance

class Performance(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    METRIC_KEY_FIELD_NUMBER: builtins.int
    PERFORMANCE_VALUE_FIELD_NUMBER: builtins.int
    CREATION_DATE_FIELD_NUMBER: builtins.int
    compute_task_key: typing.Text = ...
    metric_key: typing.Text = ...
    performance_value: builtins.float = ...
    @property
    def creation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    def __init__(self,
        *,
        compute_task_key : typing.Text = ...,
        metric_key : typing.Text = ...,
        performance_value : builtins.float = ...,
        creation_date : typing.Optional[google.protobuf.timestamp_pb2.Timestamp] = ...,
        ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["creation_date",b"creation_date"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_task_key",b"compute_task_key","creation_date",b"creation_date","metric_key",b"metric_key","performance_value",b"performance_value"]) -> None: ...
global___Performance = Performance

class PerformanceQueryFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    METRIC_KEY_FIELD_NUMBER: builtins.int
    compute_task_key: typing.Text = ...
    metric_key: typing.Text = ...
    def __init__(self,
        *,
        compute_task_key : typing.Text = ...,
        metric_key : typing.Text = ...,
        ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_task_key",b"compute_task_key","metric_key",b"metric_key"]) -> None: ...
global___PerformanceQueryFilter = PerformanceQueryFilter

class QueryPerformancesParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    PAGE_TOKEN_FIELD_NUMBER: builtins.int
    PAGE_SIZE_FIELD_NUMBER: builtins.int
    FILTER_FIELD_NUMBER: builtins.int
    page_token: typing.Text = ...
    page_size: builtins.int = ...
    @property
    def filter(self) -> global___PerformanceQueryFilter: ...
    def __init__(self,
        *,
        page_token : typing.Text = ...,
        page_size : builtins.int = ...,
        filter : typing.Optional[global___PerformanceQueryFilter] = ...,
        ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["filter",b"filter"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["filter",b"filter","page_size",b"page_size","page_token",b"page_token"]) -> None: ...
global___QueryPerformancesParam = QueryPerformancesParam

class QueryPerformancesResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    PERFORMANCES_FIELD_NUMBER: builtins.int
    NEXT_PAGE_TOKEN_FIELD_NUMBER: builtins.int
    @property
    def Performances(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Performance]: ...
    next_page_token: typing.Text = ...
    def __init__(self,
        *,
        Performances : typing.Optional[typing.Iterable[global___Performance]] = ...,
        next_page_token : typing.Text = ...,
        ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["Performances",b"Performances","next_page_token",b"next_page_token"]) -> None: ...
global___QueryPerformancesResponse = QueryPerformancesResponse