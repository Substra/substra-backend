"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import algo_pb2
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

class _ComputeTaskCategory:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ComputeTaskCategoryEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ComputeTaskCategory.ValueType], builtins.type):  # noqa: F821
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    TASK_UNKNOWN: _ComputeTaskCategory.ValueType  # 0
    TASK_TRAIN: _ComputeTaskCategory.ValueType  # 1
    TASK_AGGREGATE: _ComputeTaskCategory.ValueType  # 2
    TASK_COMPOSITE: _ComputeTaskCategory.ValueType  # 3
    TASK_TEST: _ComputeTaskCategory.ValueType  # 4
    TASK_PREDICT: _ComputeTaskCategory.ValueType  # 5

class ComputeTaskCategory(_ComputeTaskCategory, metaclass=_ComputeTaskCategoryEnumTypeWrapper): ...

TASK_UNKNOWN: ComputeTaskCategory.ValueType  # 0
TASK_TRAIN: ComputeTaskCategory.ValueType  # 1
TASK_AGGREGATE: ComputeTaskCategory.ValueType  # 2
TASK_COMPOSITE: ComputeTaskCategory.ValueType  # 3
TASK_TEST: ComputeTaskCategory.ValueType  # 4
TASK_PREDICT: ComputeTaskCategory.ValueType  # 5
global___ComputeTaskCategory = ComputeTaskCategory

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
    CATEGORY_FIELD_NUMBER: builtins.int
    ALGO_FIELD_NUMBER: builtins.int
    OWNER_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    PARENT_TASK_KEYS_FIELD_NUMBER: builtins.int
    RANK_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    WORKER_FIELD_NUMBER: builtins.int
    CREATION_DATE_FIELD_NUMBER: builtins.int
    LOGS_PERMISSION_FIELD_NUMBER: builtins.int
    TEST_FIELD_NUMBER: builtins.int
    TRAIN_FIELD_NUMBER: builtins.int
    COMPOSITE_FIELD_NUMBER: builtins.int
    AGGREGATE_FIELD_NUMBER: builtins.int
    PREDICT_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    key: builtins.str
    category: global___ComputeTaskCategory.ValueType
    @property
    def algo(self) -> algo_pb2.Algo: ...
    owner: builtins.str
    compute_plan_key: builtins.str
    @property
    def parent_task_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]:
        """Keys of parent ComputeTasks"""
    rank: builtins.int
    status: global___ComputeTaskStatus.ValueType
    """mutable"""
    worker: builtins.str
    @property
    def creation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def logs_permission(self) -> common_pb2.Permission: ...
    @property
    def test(self) -> global___TestTaskData: ...
    @property
    def train(self) -> global___TrainTaskData: ...
    @property
    def composite(self) -> global___CompositeTrainTaskData: ...
    @property
    def aggregate(self) -> global___AggregateTrainTaskData: ...
    @property
    def predict(self) -> global___PredictTaskData: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def inputs(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ComputeTaskInput]: ...
    @property
    def outputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___ComputeTaskOutput]: ...
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        category: global___ComputeTaskCategory.ValueType = ...,
        algo: algo_pb2.Algo | None = ...,
        owner: builtins.str = ...,
        compute_plan_key: builtins.str = ...,
        parent_task_keys: collections.abc.Iterable[builtins.str] | None = ...,
        rank: builtins.int = ...,
        status: global___ComputeTaskStatus.ValueType = ...,
        worker: builtins.str = ...,
        creation_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        logs_permission: common_pb2.Permission | None = ...,
        test: global___TestTaskData | None = ...,
        train: global___TrainTaskData | None = ...,
        composite: global___CompositeTrainTaskData | None = ...,
        aggregate: global___AggregateTrainTaskData | None = ...,
        predict: global___PredictTaskData | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Iterable[global___ComputeTaskInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___ComputeTaskOutput] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["aggregate", b"aggregate", "algo", b"algo", "composite", b"composite", "creation_date", b"creation_date", "data", b"data", "logs_permission", b"logs_permission", "predict", b"predict", "test", b"test", "train", b"train"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["aggregate", b"aggregate", "algo", b"algo", "category", b"category", "composite", b"composite", "compute_plan_key", b"compute_plan_key", "creation_date", b"creation_date", "data", b"data", "inputs", b"inputs", "key", b"key", "logs_permission", b"logs_permission", "metadata", b"metadata", "outputs", b"outputs", "owner", b"owner", "parent_task_keys", b"parent_task_keys", "predict", b"predict", "rank", b"rank", "status", b"status", "test", b"test", "train", b"train", "worker", b"worker"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["data", b"data"]) -> typing_extensions.Literal["test", "train", "composite", "aggregate", "predict"] | None: ...

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
    CATEGORY_FIELD_NUMBER: builtins.int
    ALGO_KEY_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    WORKER_FIELD_NUMBER: builtins.int
    PARENT_TASK_KEYS_FIELD_NUMBER: builtins.int
    TEST_FIELD_NUMBER: builtins.int
    TRAIN_FIELD_NUMBER: builtins.int
    COMPOSITE_FIELD_NUMBER: builtins.int
    AGGREGATE_FIELD_NUMBER: builtins.int
    PREDICT_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    key: builtins.str
    category: global___ComputeTaskCategory.ValueType
    algo_key: builtins.str
    compute_plan_key: builtins.str
    worker: builtins.str
    @property
    def parent_task_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]:
        """This property is now ignored, task parents are determined from the inputs."""
    @property
    def test(self) -> global___NewTestTaskData: ...
    @property
    def train(self) -> global___NewTrainTaskData: ...
    @property
    def composite(self) -> global___NewCompositeTrainTaskData: ...
    @property
    def aggregate(self) -> global___NewAggregateTrainTaskData: ...
    @property
    def predict(self) -> global___NewPredictTaskData: ...
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
        category: global___ComputeTaskCategory.ValueType = ...,
        algo_key: builtins.str = ...,
        compute_plan_key: builtins.str = ...,
        worker: builtins.str = ...,
        parent_task_keys: collections.abc.Iterable[builtins.str] | None = ...,
        test: global___NewTestTaskData | None = ...,
        train: global___NewTrainTaskData | None = ...,
        composite: global___NewCompositeTrainTaskData | None = ...,
        aggregate: global___NewAggregateTrainTaskData | None = ...,
        predict: global___NewPredictTaskData | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Iterable[global___ComputeTaskInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___NewComputeTaskOutput] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["aggregate", b"aggregate", "composite", b"composite", "data", b"data", "predict", b"predict", "test", b"test", "train", b"train"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["aggregate", b"aggregate", "algo_key", b"algo_key", "category", b"category", "composite", b"composite", "compute_plan_key", b"compute_plan_key", "data", b"data", "inputs", b"inputs", "key", b"key", "metadata", b"metadata", "outputs", b"outputs", "parent_task_keys", b"parent_task_keys", "predict", b"predict", "test", b"test", "train", b"train", "worker", b"worker"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["data", b"data"]) -> typing_extensions.Literal["test", "train", "composite", "aggregate", "predict"] | None: ...

global___NewComputeTask = NewComputeTask

class TrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___TrainTaskData = TrainTaskData

class NewTrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___NewTrainTaskData = NewTrainTaskData

class PredictTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___PredictTaskData = PredictTaskData

class NewPredictTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___NewPredictTaskData = NewPredictTaskData

class TestTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___TestTaskData = TestTaskData

class NewTestTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___NewTestTaskData = NewTestTaskData

class CompositeTrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___CompositeTrainTaskData = CompositeTrainTaskData

class NewCompositeTrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DATA_MANAGER_KEY_FIELD_NUMBER: builtins.int
    DATA_SAMPLE_KEYS_FIELD_NUMBER: builtins.int
    data_manager_key: builtins.str
    @property
    def data_sample_keys(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    def __init__(
        self,
        *,
        data_manager_key: builtins.str = ...,
        data_sample_keys: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["data_manager_key", b"data_manager_key", "data_sample_keys", b"data_sample_keys"]) -> None: ...

global___NewCompositeTrainTaskData = NewCompositeTrainTaskData

class AggregateTrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___AggregateTrainTaskData = AggregateTrainTaskData

class NewAggregateTrainTaskData(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WORKER_FIELD_NUMBER: builtins.int
    worker: builtins.str
    """worker property is deprecated, pass the worker through NewComputeTask.Worker"""
    def __init__(
        self,
        *,
        worker: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["worker", b"worker"]) -> None: ...

global___NewAggregateTrainTaskData = NewAggregateTrainTaskData

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
    CATEGORY_FIELD_NUMBER: builtins.int
    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    ALGO_KEY_FIELD_NUMBER: builtins.int
    worker: builtins.str
    status: global___ComputeTaskStatus.ValueType
    category: global___ComputeTaskCategory.ValueType
    compute_plan_key: builtins.str
    algo_key: builtins.str
    def __init__(
        self,
        *,
        worker: builtins.str = ...,
        status: global___ComputeTaskStatus.ValueType = ...,
        category: global___ComputeTaskCategory.ValueType = ...,
        compute_plan_key: builtins.str = ...,
        algo_key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["algo_key", b"algo_key", "category", b"category", "compute_plan_key", b"compute_plan_key", "status", b"status", "worker", b"worker"]) -> None: ...

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
