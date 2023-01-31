"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import algo_pb2
import builtins
import collections.abc
import common_pb2
import computeplan_pb2
import computetask_pb2
import datamanager_pb2
import datasample_pb2
import failure_report_pb2
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import model_pb2
import organization_pb2
import performance_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _EventKind:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _EventKindEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_EventKind.ValueType], builtins.type):  # noqa: F821
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    EVENT_UNKNOWN: _EventKind.ValueType  # 0
    EVENT_ASSET_CREATED: _EventKind.ValueType  # 1
    EVENT_ASSET_UPDATED: _EventKind.ValueType  # 2
    EVENT_ASSET_DISABLED: _EventKind.ValueType  # 3

class EventKind(_EventKind, metaclass=_EventKindEnumTypeWrapper): ...

EVENT_UNKNOWN: EventKind.ValueType  # 0
EVENT_ASSET_CREATED: EventKind.ValueType  # 1
EVENT_ASSET_UPDATED: EventKind.ValueType  # 2
EVENT_ASSET_DISABLED: EventKind.ValueType  # 3
global___EventKind = EventKind

class Event(google.protobuf.message.Message):
    """Event is an occurrence of an orchestration event.
    It is triggered during orchestration and allows a consumer to react to the orchestration process.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class MetadataEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    ID_FIELD_NUMBER: builtins.int
    ASSET_KEY_FIELD_NUMBER: builtins.int
    ASSET_KIND_FIELD_NUMBER: builtins.int
    EVENT_KIND_FIELD_NUMBER: builtins.int
    CHANNEL_FIELD_NUMBER: builtins.int
    TIMESTAMP_FIELD_NUMBER: builtins.int
    ALGO_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_FIELD_NUMBER: builtins.int
    COMPUTE_TASK_FIELD_NUMBER: builtins.int
    DATA_MANAGER_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_FIELD_NUMBER: builtins.int
    FAILURE_REPORT_FIELD_NUMBER: builtins.int
    MODEL_FIELD_NUMBER: builtins.int
    ORGANIZATION_FIELD_NUMBER: builtins.int
    PERFORMANCE_FIELD_NUMBER: builtins.int
    COMPUTE_TASK_OUTPUT_ASSET_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    id: builtins.str
    asset_key: builtins.str
    asset_kind: common_pb2.AssetKind.ValueType
    event_kind: global___EventKind.ValueType
    channel: builtins.str
    @property
    def timestamp(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def function(self) -> algo_pb2.Algo: ...
    @property
    def compute_plan(self) -> computeplan_pb2.ComputePlan: ...
    @property
    def compute_task(self) -> computetask_pb2.ComputeTask: ...
    @property
    def data_manager(self) -> datamanager_pb2.DataManager: ...
    @property
    def data_sample(self) -> datasample_pb2.DataSample: ...
    @property
    def failure_report(self) -> failure_report_pb2.FailureReport: ...
    @property
    def model(self) -> model_pb2.Model: ...
    @property
    def organization(self) -> organization_pb2.Organization: ...
    @property
    def performance(self) -> performance_pb2.Performance: ...
    @property
    def compute_task_output_asset(self) -> computetask_pb2.ComputeTaskOutputAsset: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    def __init__(
        self,
        *,
        id: builtins.str = ...,
        asset_key: builtins.str = ...,
        asset_kind: common_pb2.AssetKind.ValueType = ...,
        event_kind: global___EventKind.ValueType = ...,
        channel: builtins.str = ...,
        timestamp: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        function: algo_pb2.Algo | None = ...,
        compute_plan: computeplan_pb2.ComputePlan | None = ...,
        compute_task: computetask_pb2.ComputeTask | None = ...,
        data_manager: datamanager_pb2.DataManager | None = ...,
        data_sample: datasample_pb2.DataSample | None = ...,
        failure_report: failure_report_pb2.FailureReport | None = ...,
        model: model_pb2.Model | None = ...,
        organization: organization_pb2.Organization | None = ...,
        performance: performance_pb2.Performance | None = ...,
        compute_task_output_asset: computetask_pb2.ComputeTaskOutputAsset | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["function", b"function", "asset", b"asset", "compute_plan", b"compute_plan", "compute_task", b"compute_task", "compute_task_output_asset", b"compute_task_output_asset", "data_manager", b"data_manager", "data_sample", b"data_sample", "failure_report", b"failure_report", "model", b"model", "organization", b"organization", "performance", b"performance", "timestamp", b"timestamp"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["function", b"function", "asset", b"asset", "asset_key", b"asset_key", "asset_kind", b"asset_kind", "channel", b"channel", "compute_plan", b"compute_plan", "compute_task", b"compute_task", "compute_task_output_asset", b"compute_task_output_asset", "data_manager", b"data_manager", "data_sample", b"data_sample", "event_kind", b"event_kind", "failure_report", b"failure_report", "id", b"id", "metadata", b"metadata", "model", b"model", "organization", b"organization", "performance", b"performance", "timestamp", b"timestamp"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["asset", b"asset"]) -> typing_extensions.Literal["function", "compute_plan", "compute_task", "data_manager", "data_sample", "failure_report", "model", "organization", "performance", "compute_task_output_asset"] | None: ...

global___Event = Event

class QueryEventsParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PAGE_TOKEN_FIELD_NUMBER: builtins.int
    PAGE_SIZE_FIELD_NUMBER: builtins.int
    FILTER_FIELD_NUMBER: builtins.int
    SORT_FIELD_NUMBER: builtins.int
    page_token: builtins.str
    page_size: builtins.int
    @property
    def filter(self) -> global___EventQueryFilter: ...
    sort: common_pb2.SortOrder.ValueType
    def __init__(
        self,
        *,
        page_token: builtins.str = ...,
        page_size: builtins.int = ...,
        filter: global___EventQueryFilter | None = ...,
        sort: common_pb2.SortOrder.ValueType = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["filter", b"filter"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["filter", b"filter", "page_size", b"page_size", "page_token", b"page_token", "sort", b"sort"]) -> None: ...

global___QueryEventsParam = QueryEventsParam

class EventQueryFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class MetadataEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    ASSET_KEY_FIELD_NUMBER: builtins.int
    ASSET_KIND_FIELD_NUMBER: builtins.int
    EVENT_KIND_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    START_FIELD_NUMBER: builtins.int
    END_FIELD_NUMBER: builtins.int
    asset_key: builtins.str
    asset_kind: common_pb2.AssetKind.ValueType
    event_kind: global___EventKind.ValueType
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def start(self) -> google.protobuf.timestamp_pb2.Timestamp:
        """timestamp inclusive lower bound"""
    @property
    def end(self) -> google.protobuf.timestamp_pb2.Timestamp:
        """timestamp inclusive upper bound"""
    def __init__(
        self,
        *,
        asset_key: builtins.str = ...,
        asset_kind: common_pb2.AssetKind.ValueType = ...,
        event_kind: global___EventKind.ValueType = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        start: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        end: google.protobuf.timestamp_pb2.Timestamp | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["end", b"end", "start", b"start"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset_key", b"asset_key", "asset_kind", b"asset_kind", "end", b"end", "event_kind", b"event_kind", "metadata", b"metadata", "start", b"start"]) -> None: ...

global___EventQueryFilter = EventQueryFilter

class QueryEventsResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    EVENTS_FIELD_NUMBER: builtins.int
    NEXT_PAGE_TOKEN_FIELD_NUMBER: builtins.int
    @property
    def events(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Event]: ...
    next_page_token: builtins.str
    def __init__(
        self,
        *,
        events: collections.abc.Iterable[global___Event] | None = ...,
        next_page_token: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["events", b"events", "next_page_token", b"next_page_token"]) -> None: ...

global___QueryEventsResponse = QueryEventsResponse

class SubscribeToEventsParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    START_EVENT_ID_FIELD_NUMBER: builtins.int
    start_event_id: builtins.str
    """Start streaming events from this ID (excluding)"""
    def __init__(
        self,
        *,
        start_event_id: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["start_event_id", b"start_event_id"]) -> None: ...

global___SubscribeToEventsParam = SubscribeToEventsParam
