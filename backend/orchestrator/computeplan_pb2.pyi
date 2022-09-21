"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _ComputePlanAction:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ComputePlanActionEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ComputePlanAction.ValueType], builtins.type):  # noqa: F821
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    PLAN_ACTION_UNKNOWN: _ComputePlanAction.ValueType  # 0
    PLAN_ACTION_CANCELED: _ComputePlanAction.ValueType  # 1

class ComputePlanAction(_ComputePlanAction, metaclass=_ComputePlanActionEnumTypeWrapper): ...

PLAN_ACTION_UNKNOWN: ComputePlanAction.ValueType  # 0
PLAN_ACTION_CANCELED: ComputePlanAction.ValueType  # 1
global___ComputePlanAction = ComputePlanAction

class ComputePlan(google.protobuf.message.Message):
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

    KEY_FIELD_NUMBER: builtins.int
    OWNER_FIELD_NUMBER: builtins.int
    DELETE_INTERMEDIARY_MODELS_FIELD_NUMBER: builtins.int
    CREATION_DATE_FIELD_NUMBER: builtins.int
    TAG_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    CANCELATION_DATE_FIELD_NUMBER: builtins.int
    FAILURE_DATE_FIELD_NUMBER: builtins.int
    key: builtins.str
    owner: builtins.str
    delete_intermediary_models: builtins.bool
    @property
    def creation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    tag: builtins.str
    name: builtins.str
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def cancelation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def failure_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        owner: builtins.str = ...,
        delete_intermediary_models: builtins.bool = ...,
        creation_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        tag: builtins.str = ...,
        name: builtins.str = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        cancelation_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        failure_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["cancelation_date", b"cancelation_date", "creation_date", b"creation_date", "failure_date", b"failure_date"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["cancelation_date", b"cancelation_date", "creation_date", b"creation_date", "delete_intermediary_models", b"delete_intermediary_models", "failure_date", b"failure_date", "key", b"key", "metadata", b"metadata", "name", b"name", "owner", b"owner", "tag", b"tag"]) -> None: ...

global___ComputePlan = ComputePlan

class NewComputePlan(google.protobuf.message.Message):
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

    KEY_FIELD_NUMBER: builtins.int
    TAG_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    DELETE_INTERMEDIARY_MODELS_FIELD_NUMBER: builtins.int
    key: builtins.str
    tag: builtins.str
    name: builtins.str
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    delete_intermediary_models: builtins.bool
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        tag: builtins.str = ...,
        name: builtins.str = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        delete_intermediary_models: builtins.bool = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["delete_intermediary_models", b"delete_intermediary_models", "key", b"key", "metadata", b"metadata", "name", b"name", "tag", b"tag"]) -> None: ...

global___NewComputePlan = NewComputePlan

class GetComputePlanParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key"]) -> None: ...

global___GetComputePlanParam = GetComputePlanParam

class ApplyPlanActionParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    ACTION_FIELD_NUMBER: builtins.int
    key: builtins.str
    action: global___ComputePlanAction.ValueType
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        action: global___ComputePlanAction.ValueType = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["action", b"action", "key", b"key"]) -> None: ...

global___ApplyPlanActionParam = ApplyPlanActionParam

class ApplyPlanActionResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ApplyPlanActionResponse = ApplyPlanActionResponse

class PlanQueryFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    OWNER_FIELD_NUMBER: builtins.int
    owner: builtins.str
    def __init__(
        self,
        *,
        owner: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["owner", b"owner"]) -> None: ...

global___PlanQueryFilter = PlanQueryFilter

class QueryPlansParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PAGE_TOKEN_FIELD_NUMBER: builtins.int
    PAGE_SIZE_FIELD_NUMBER: builtins.int
    FILTER_FIELD_NUMBER: builtins.int
    page_token: builtins.str
    page_size: builtins.int
    @property
    def filter(self) -> global___PlanQueryFilter: ...
    def __init__(
        self,
        *,
        page_token: builtins.str = ...,
        page_size: builtins.int = ...,
        filter: global___PlanQueryFilter | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["filter", b"filter"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["filter", b"filter", "page_size", b"page_size", "page_token", b"page_token"]) -> None: ...

global___QueryPlansParam = QueryPlansParam

class QueryPlansResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PLANS_FIELD_NUMBER: builtins.int
    NEXT_PAGE_TOKEN_FIELD_NUMBER: builtins.int
    @property
    def plans(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputePlan]: ...
    next_page_token: builtins.str
    def __init__(
        self,
        *,
        plans: collections.abc.Iterable[global___ComputePlan] | None = ...,
        next_page_token: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["next_page_token", b"next_page_token", "plans", b"plans"]) -> None: ...

global___QueryPlansResponse = QueryPlansResponse

class UpdateComputePlanParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    key: builtins.str
    name: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        name: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "name", b"name"]) -> None: ...

global___UpdateComputePlanParam = UpdateComputePlanParam

class UpdateComputePlanResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___UpdateComputePlanResponse = UpdateComputePlanResponse

class IsPlanRunningParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key"]) -> None: ...

global___IsPlanRunningParam = IsPlanRunningParam

class IsPlanRunningResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    IS_RUNNING_FIELD_NUMBER: builtins.int
    is_running: builtins.bool
    def __init__(
        self,
        *,
        is_running: builtins.bool = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["is_running", b"is_running"]) -> None: ...

global___IsPlanRunningResponse = IsPlanRunningResponse
