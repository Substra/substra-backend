"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import common_pb2
import datamanager_pb2
import datasample_pb2
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import model_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _ComputeTaskStatus:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ComputeTaskStatusEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ComputeTaskStatus.ValueType], builtins.type):  # noqa: F821
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    STATUS_UNKNOWN: _ComputeTaskStatus.ValueType  # 0
    STATUS_WAITING: _ComputeTaskStatus.ValueType  # 1
    STATUS_TODO: _ComputeTaskStatus.ValueType  # 2
    STATUS_DOING: _ComputeTaskStatus.ValueType  # 3
    STATUS_DONE: _ComputeTaskStatus.ValueType  # 4
    STATUS_CANCELED: _ComputeTaskStatus.ValueType  # 5
    STATUS_FAILED: _ComputeTaskStatus.ValueType  # 6

class ComputeTaskStatus(_ComputeTaskStatus, metaclass=_ComputeTaskStatusEnumTypeWrapper): ...

STATUS_UNKNOWN: ComputeTaskStatus.ValueType  # 0
STATUS_WAITING: ComputeTaskStatus.ValueType  # 1
STATUS_TODO: ComputeTaskStatus.ValueType  # 2
STATUS_DOING: ComputeTaskStatus.ValueType  # 3
STATUS_DONE: ComputeTaskStatus.ValueType  # 4
STATUS_CANCELED: ComputeTaskStatus.ValueType  # 5
STATUS_FAILED: ComputeTaskStatus.ValueType  # 6
global___ComputeTaskStatus = ComputeTaskStatus

class _ComputeTaskAction:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ComputeTaskActionEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ComputeTaskAction.ValueType], builtins.type):  # noqa: F821
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    TASK_ACTION_UNKNOWN: _ComputeTaskAction.ValueType  # 0
    TASK_ACTION_DOING: _ComputeTaskAction.ValueType  # 1
    TASK_ACTION_CANCELED: _ComputeTaskAction.ValueType  # 2
    TASK_ACTION_FAILED: _ComputeTaskAction.ValueType  # 3
    TASK_ACTION_DONE: _ComputeTaskAction.ValueType  # 4

class ComputeTaskAction(_ComputeTaskAction, metaclass=_ComputeTaskActionEnumTypeWrapper): ...

TASK_ACTION_UNKNOWN: ComputeTaskAction.ValueType  # 0
TASK_ACTION_DOING: ComputeTaskAction.ValueType  # 1
TASK_ACTION_CANCELED: ComputeTaskAction.ValueType  # 2
TASK_ACTION_FAILED: ComputeTaskAction.ValueType  # 3
TASK_ACTION_DONE: ComputeTaskAction.ValueType  # 4
global___ComputeTaskAction = ComputeTaskAction

class ParentTaskOutputRef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PARENT_TASK_KEY_FIELD_NUMBER: builtins.int
    OUTPUT_IDENTIFIER_FIELD_NUMBER: builtins.int
    parent_task_key: builtins.str
    output_identifier: builtins.str
    def __init__(
        self,
        *,
        parent_task_key: builtins.str = ...,
        output_identifier: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["output_identifier", b"output_identifier", "parent_task_key", b"parent_task_key"]) -> None: ...

global___ParentTaskOutputRef = ParentTaskOutputRef

class ComputeTaskInput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    IDENTIFIER_FIELD_NUMBER: builtins.int
    ASSET_KEY_FIELD_NUMBER: builtins.int
    PARENT_TASK_OUTPUT_FIELD_NUMBER: builtins.int
    identifier: builtins.str
    asset_key: builtins.str
    @property
    def parent_task_output(self) -> global___ParentTaskOutputRef: ...
    def __init__(
        self,
        *,
        identifier: builtins.str = ...,
        asset_key: builtins.str = ...,
        parent_task_output: global___ParentTaskOutputRef | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["asset_key", b"asset_key", "parent_task_output", b"parent_task_output", "ref", b"ref"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset_key", b"asset_key", "identifier", b"identifier", "parent_task_output", b"parent_task_output", "ref", b"ref"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["ref", b"ref"]) -> typing_extensions.Literal["asset_key", "parent_task_output"] | None: ...

global___ComputeTaskInput = ComputeTaskInput

class ComputeTaskOutput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PERMISSIONS_FIELD_NUMBER: builtins.int
    TRANSIENT_FIELD_NUMBER: builtins.int
    @property
    def permissions(self) -> common_pb2.Permissions: ...
    transient: builtins.bool
    def __init__(
        self,
        *,
        permissions: common_pb2.Permissions | None = ...,
        transient: builtins.bool = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["permissions", b"permissions"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["permissions", b"permissions", "transient", b"transient"]) -> None: ...

global___ComputeTaskOutput = ComputeTaskOutput

class NewComputeTaskOutput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PERMISSIONS_FIELD_NUMBER: builtins.int
    TRANSIENT_FIELD_NUMBER: builtins.int
    @property
    def permissions(self) -> common_pb2.NewPermissions: ...
    transient: builtins.bool
    def __init__(
        self,
        *,
        permissions: common_pb2.NewPermissions | None = ...,
        transient: builtins.bool = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["permissions", b"permissions"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["permissions", b"permissions", "transient", b"transient"]) -> None: ...

global___NewComputeTaskOutput = NewComputeTaskOutput

class ComputeTask(google.protobuf.message.Message):
    """ComputeTask is a computation step in a ComputePlan.
    It was previously called XXXtuple: Traintuple, CompositeTraintuple, etc
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

    class OutputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___ComputeTaskOutput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___ComputeTaskOutput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    KEY_FIELD_NUMBER: builtins.int
    OWNER_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    RANK_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    WORKER_FIELD_NUMBER: builtins.int
    CREATION_DATE_FIELD_NUMBER: builtins.int
    LOGS_PERMISSION_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    FUNCTION_KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    owner: builtins.str
    compute_plan_key: builtins.str
    rank: builtins.int
    """Keys of parent ComputeTasks"""
    status: global___ComputeTaskStatus.ValueType
    """mutable"""
    worker: builtins.str
    @property
    def creation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def logs_permission(self) -> common_pb2.Permission: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def inputs(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTaskInput]: ...
    @property
    def outputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___ComputeTaskOutput]: ...
    function_key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        owner: builtins.str = ...,
        compute_plan_key: builtins.str = ...,
        rank: builtins.int = ...,
        status: global___ComputeTaskStatus.ValueType = ...,
        worker: builtins.str = ...,
        creation_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        logs_permission: common_pb2.Permission | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Iterable[global___ComputeTaskInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___ComputeTaskOutput] | None = ...,
        function_key: builtins.str = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["creation_date", b"creation_date", "logs_permission", b"logs_permission"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_plan_key", b"compute_plan_key", "creation_date", b"creation_date", "function_key", b"function_key", "inputs", b"inputs", "key", b"key", "logs_permission", b"logs_permission", "metadata", b"metadata", "outputs", b"outputs", "owner", b"owner", "rank", b"rank", "status", b"status", "worker", b"worker"]) -> None: ...

global___ComputeTask = ComputeTask

class NewComputeTask(google.protobuf.message.Message):
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

    class OutputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___NewComputeTaskOutput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___NewComputeTaskOutput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    KEY_FIELD_NUMBER: builtins.int
    FUNCTION_KEY_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    WORKER_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    key: builtins.str
    function_key: builtins.str
    compute_plan_key: builtins.str
    worker: builtins.str
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def inputs(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTaskInput]: ...
    @property
    def outputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___NewComputeTaskOutput]: ...
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        function_key: builtins.str = ...,
        compute_plan_key: builtins.str = ...,
        worker: builtins.str = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Iterable[global___ComputeTaskInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___NewComputeTaskOutput] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_plan_key", b"compute_plan_key", "function_key", b"function_key", "inputs", b"inputs", "key", b"key", "metadata", b"metadata", "outputs", b"outputs", "worker", b"worker"]) -> None: ...

global___NewComputeTask = NewComputeTask

class RegisterTasksParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    TASKS_FIELD_NUMBER: builtins.int
    @property
    def tasks(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___NewComputeTask]: ...
    def __init__(
        self,
        *,
        tasks: collections.abc.Iterable[global___NewComputeTask] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["tasks", b"tasks"]) -> None: ...

global___RegisterTasksParam = RegisterTasksParam

class RegisterTasksResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    TASKS_FIELD_NUMBER: builtins.int
    @property
    def tasks(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTask]: ...
    def __init__(
        self,
        *,
        tasks: collections.abc.Iterable[global___ComputeTask] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["tasks", b"tasks"]) -> None: ...

global___RegisterTasksResponse = RegisterTasksResponse

class TaskQueryFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WORKER_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    FUNCTION_KEY_FIELD_NUMBER: builtins.int
    worker: builtins.str
    status: global___ComputeTaskStatus.ValueType
    compute_plan_key: builtins.str
    function_key: builtins.str
    def __init__(
        self,
        *,
        worker: builtins.str = ...,
        status: global___ComputeTaskStatus.ValueType = ...,
        compute_plan_key: builtins.str = ...,
        function_key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_plan_key", b"compute_plan_key", "function_key", b"function_key", "status", b"status", "worker", b"worker"]) -> None: ...

global___TaskQueryFilter = TaskQueryFilter

class QueryTasksParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PAGE_TOKEN_FIELD_NUMBER: builtins.int
    PAGE_SIZE_FIELD_NUMBER: builtins.int
    FILTER_FIELD_NUMBER: builtins.int
    page_token: builtins.str
    page_size: builtins.int
    @property
    def filter(self) -> global___TaskQueryFilter: ...
    def __init__(
        self,
        *,
        page_token: builtins.str = ...,
        page_size: builtins.int = ...,
        filter: global___TaskQueryFilter | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["filter", b"filter"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["filter", b"filter", "page_size", b"page_size", "page_token", b"page_token"]) -> None: ...

global___QueryTasksParam = QueryTasksParam

class QueryTasksResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    TASKS_FIELD_NUMBER: builtins.int
    NEXT_PAGE_TOKEN_FIELD_NUMBER: builtins.int
    @property
    def tasks(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTask]: ...
    next_page_token: builtins.str
    def __init__(
        self,
        *,
        tasks: collections.abc.Iterable[global___ComputeTask] | None = ...,
        next_page_token: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["next_page_token", b"next_page_token", "tasks", b"tasks"]) -> None: ...

global___QueryTasksResponse = QueryTasksResponse

class GetTaskParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key"]) -> None: ...

global___GetTaskParam = GetTaskParam

class ComputeTaskOutputAsset(google.protobuf.message.Message):
    """ComputeTaskOutputAsset links an asset to a task output.
    It is not exposed through gRPC methods, but will be sent as event.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    COMPUTE_TASK_OUTPUT_IDENTIFIER_FIELD_NUMBER: builtins.int
    ASSET_KIND_FIELD_NUMBER: builtins.int
    ASSET_KEY_FIELD_NUMBER: builtins.int
    compute_task_key: builtins.str
    compute_task_output_identifier: builtins.str
    asset_kind: common_pb2.AssetKind.ValueType
    asset_key: builtins.str
    def __init__(
        self,
        *,
        compute_task_key: builtins.str = ...,
        compute_task_output_identifier: builtins.str = ...,
        asset_kind: common_pb2.AssetKind.ValueType = ...,
        asset_key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset_key", b"asset_key", "asset_kind", b"asset_kind", "compute_task_key", b"compute_task_key", "compute_task_output_identifier", b"compute_task_output_identifier"]) -> None: ...

global___ComputeTaskOutputAsset = ComputeTaskOutputAsset

class ApplyTaskActionParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    ACTION_FIELD_NUMBER: builtins.int
    LOG_FIELD_NUMBER: builtins.int
    compute_task_key: builtins.str
    action: global___ComputeTaskAction.ValueType
    log: builtins.str
    def __init__(
        self,
        *,
        compute_task_key: builtins.str = ...,
        action: global___ComputeTaskAction.ValueType = ...,
        log: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["action", b"action", "compute_task_key", b"compute_task_key", "log", b"log"]) -> None: ...

global___ApplyTaskActionParam = ApplyTaskActionParam

class ApplyTaskActionResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ApplyTaskActionResponse = ApplyTaskActionResponse

class ComputeTaskInputAsset(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    IDENTIFIER_FIELD_NUMBER: builtins.int
    MODEL_FIELD_NUMBER: builtins.int
    DATA_MANAGER_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_FIELD_NUMBER: builtins.int
    identifier: builtins.str
    @property
    def model(self) -> model_pb2.Model: ...
    @property
    def data_manager(self) -> datamanager_pb2.DataManager: ...
    @property
    def data_sample(self) -> datasample_pb2.DataSample: ...
    def __init__(
        self,
        *,
        identifier: builtins.str = ...,
        model: model_pb2.Model | None = ...,
        data_manager: datamanager_pb2.DataManager | None = ...,
        data_sample: datasample_pb2.DataSample | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["asset", b"asset", "data_manager", b"data_manager", "data_sample", b"data_sample", "model", b"model"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["asset", b"asset", "data_manager", b"data_manager", "data_sample", b"data_sample", "identifier", b"identifier", "model", b"model"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["asset", b"asset"]) -> typing_extensions.Literal["model", "data_manager", "data_sample"] | None: ...

global___ComputeTaskInputAsset = ComputeTaskInputAsset

class GetTaskInputAssetsParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    compute_task_key: builtins.str
    def __init__(
        self,
        *,
        compute_task_key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_task_key", b"compute_task_key"]) -> None: ...

global___GetTaskInputAssetsParam = GetTaskInputAssetsParam

class GetTaskInputAssetsResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ASSETS_FIELD_NUMBER: builtins.int
    @property
    def assets(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTaskInputAsset]: ...
    def __init__(
        self,
        *,
        assets: collections.abc.Iterable[global___ComputeTaskInputAsset] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["assets", b"assets"]) -> None: ...

global___GetTaskInputAssetsResponse = GetTaskInputAssetsResponse

class DisableOutputParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    COMPUTE_TASK_KEY_FIELD_NUMBER: builtins.int
    IDENTIFIER_FIELD_NUMBER: builtins.int
    compute_task_key: builtins.str
    identifier: builtins.str
    def __init__(
        self,
        *,
        compute_task_key: builtins.str = ...,
        identifier: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_task_key", b"compute_task_key", "identifier", b"identifier"]) -> None: ...

global___DisableOutputParam = DisableOutputParam

class DisableOutputResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___DisableOutputResponse = DisableOutputResponse
