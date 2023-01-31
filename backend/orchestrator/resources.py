from __future__ import annotations

import datetime
import enum
from typing import Optional
from typing import Union

import pydantic

from orchestrator import common_pb2
from orchestrator import computeplan_pb2
from orchestrator import computetask_pb2
from orchestrator import datamanager_pb2
from orchestrator import datasample_pb2
from orchestrator import function_pb2
from orchestrator import info_pb2
from orchestrator import model_pb2

TAG_KEY = "__tag__"


class AutoNameEnum(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):  # noqa: N805
        return name


class _Base(pydantic.BaseModel):
    def __json__(self):
        """__json__ returns the serialized representation of the class.

        This method is called by celery when passing objects around.
        """
        return self.json()


class AssetKind(AutoNameEnum):
    ASSET_UNKNOWN = enum.auto()
    ASSET_ORGANIZATION = enum.auto()
    ASSET_DATA_SAMPLE = enum.auto()
    ASSET_DATA_MANAGER = enum.auto()
    ASSET_ALGO = enum.auto()
    ASSET_COMPUTE_TASK = enum.auto()
    ASSET_COMPUTEPLAN = enum.auto()
    ASSET_MODEL = enum.auto()
    ASSET_PERFORMANCE = enum.auto()
    ASSET_FAILURE_REPORT = enum.auto()
    ASSET_COMPUTE_TASK_OUTPUT_ASSET = enum.auto()

    @classmethod
    def from_grpc(cls, k: common_pb2.AssetKind.ValueType) -> AssetKind:
        return cls(common_pb2.AssetKind.Name(k))


class Address(pydantic.BaseModel):
    uri: str
    checksum: str

    @classmethod
    def from_grpc(cls, a: common_pb2.Addressable) -> Address:
        return cls(
            uri=a.storage_address,
            checksum=a.checksum,
        )


class Model(pydantic.BaseModel):
    """Model is a partial representation of an orchestrator Model

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str
    compute_task_key: str
    address: Address
    owner: str

    @classmethod
    def from_grpc(cls, m: model_pb2.Model) -> Model:
        """Creates a Model from grpc message"""
        return cls(
            key=m.key,
            compute_task_key=m.compute_task_key,
            address=Address.from_grpc(m.address),
            owner=m.owner,
        )


class DataSample(pydantic.BaseModel):
    """DataSamples is a partial representation of an orchestrator DataSample

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str

    @classmethod
    def from_grpc(cls, s: datasample_pb2.DataSample) -> DataSample:
        """Creates a DataSample from grpc message"""
        return cls(
            key=s.key,
        )


class DataManager(pydantic.BaseModel):
    """DataManager is a partial representation of an orchestrator DataManager

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str
    opener: Address

    @classmethod
    def from_grpc(cls, m: datamanager_pb2.DataManager) -> DataManager:
        """Creates a DataManager from grpc message"""
        return cls(key=m.key, opener=Address.from_grpc(m.opener))


class FunctionInput(pydantic.BaseModel):
    kind: AssetKind
    multiple: bool
    optional: bool

    @classmethod
    def from_grpc(cls, i: function_pb2.FunctionInput) -> FunctionInput:
        return cls(kind=AssetKind.from_grpc(i.kind), multiple=i.multiple, optional=i.optional)


class FunctionOutput(pydantic.BaseModel):
    kind: AssetKind
    multiple: bool

    @classmethod
    def from_grpc(cls, o: function_pb2.FunctionOutput) -> FunctionOutput:
        return cls(kind=AssetKind.from_grpc(o.kind), multiple=o.multiple)


class Function(pydantic.BaseModel):
    key: str
    owner: str
    functionrithm: Address
    inputs: dict[str, FunctionInput]
    outputs: dict[str, FunctionOutput]

    @classmethod
    def from_grpc(cls, a: function_pb2.Function) -> Function:
        return cls(
            key=a.key,
            owner=a.owner,
            functionrithm=Address.from_grpc(a.functionrithm),
            inputs={k: FunctionInput.from_grpc(i) for k, i in a.inputs.items()},
            outputs={k: FunctionOutput.from_grpc(o) for k, o in a.outputs.items()},
        )


class ComputeTaskStatus(AutoNameEnum):
    STATUS_UNKNOWN = enum.auto()
    STATUS_WAITING = enum.auto()
    STATUS_TODO = enum.auto()
    STATUS_DOING = enum.auto()
    STATUS_DONE = enum.auto()
    STATUS_CANCELED = enum.auto()
    STATUS_FAILED = enum.auto()

    @classmethod
    def from_grpc(cls, s: computetask_pb2.ComputeTaskStatus.ValueType) -> ComputeTaskStatus:
        return cls(computetask_pb2.ComputeTaskStatus.Name(s))


class Permission(pydantic.BaseModel):
    public: bool
    authorized_ids: list[str]

    @classmethod
    def from_grpc(cls, p: common_pb2.Permission) -> Permission:
        return cls(
            public=p.public,
            authorized_ids=list(p.authorized_ids),
        )


class Permissions(pydantic.BaseModel):
    process: Permission
    download: Permission

    @classmethod
    def from_grpc(cls, p: common_pb2.Permissions) -> Permissions:
        return cls(
            process=Permission.from_grpc(p.process),
            download=Permission.from_grpc(p.download),
        )


class ComputeTaskOutput(_Base):
    permissions: Permissions
    transient: bool

    @classmethod
    def from_grpc(cls, o: computetask_pb2.ComputeTaskOutput) -> ComputeTaskOutput:
        return cls(
            permissions=Permissions.from_grpc(o.permissions),
            transient=o.transient,
        )


class ComputeTaskInput(pydantic.BaseModel):
    identifier: str
    asset_key: Optional[str]
    parent_task_key: Optional[str]
    parent_task_output_identifier: Optional[str]

    @classmethod
    def from_grpc(cls, i: computetask_pb2.ComputeTaskInput) -> ComputeTaskInput:
        direct_ref = i.WhichOneof("ref") == "asset_key"
        return cls(
            identifier=i.identifier,
            asset_key=i.asset_key if direct_ref else None,
            parent_task_key=i.parent_task_output.parent_task_key if not direct_ref else None,
            parent_task_output_identifier=i.parent_task_output.output_identifier if not direct_ref else None,
        )


class ComputeTask(_Base):
    """Task represents a generic compute task"""

    key: str
    # This property is only temporary and will disappear soon
    owner: str
    compute_plan_key: str
    function_key: str
    rank: int
    status: ComputeTaskStatus
    worker: str
    metadata: dict[str, str]
    inputs: list[ComputeTaskInput]
    outputs: dict[str, ComputeTaskOutput]
    tag: str

    @classmethod
    def from_grpc(cls, t: computetask_pb2.ComputeTask) -> ComputeTask:
        tag = t.metadata.pop(TAG_KEY, "")

        return cls(
            key=t.key,
            owner=t.owner,
            compute_plan_key=t.compute_plan_key,
            function_key=t.function_key,
            rank=t.rank,
            status=ComputeTaskStatus.from_grpc(t.status),
            worker=t.worker,
            metadata={k: v for k, v in t.metadata.items()},  # trick to have a dict instead of a grpc object
            outputs={k: ComputeTaskOutput.from_grpc(o) for k, o in t.outputs.items()},
            inputs=[ComputeTaskInput.from_grpc(i) for i in t.inputs],
            tag=tag,
        )


class ComputeTaskInputAsset(pydantic.BaseModel):
    identifier: str
    kind: AssetKind = AssetKind.ASSET_UNKNOWN
    model: Optional[Model] = None
    data_manager: Optional[DataManager] = None
    data_sample: Optional[DataSample] = None

    @classmethod
    def from_grpc(cls, input_asset: computetask_pb2.ComputeTaskInputAsset) -> ComputeTaskInputAsset:
        asset = cls(
            identifier=input_asset.identifier,
        )
        if input_asset.WhichOneof("asset") == "data_manager":
            asset.kind = AssetKind.ASSET_DATA_MANAGER
            asset.data_manager = DataManager.from_grpc(input_asset.data_manager)
        elif input_asset.WhichOneof("asset") == "data_sample":
            asset.kind = AssetKind.ASSET_DATA_SAMPLE
            asset.data_sample = DataSample.from_grpc(input_asset.data_sample)
        elif input_asset.WhichOneof("asset") == "model":
            asset.kind = AssetKind.ASSET_MODEL
            asset.model = Model.from_grpc(input_asset.model)

        return asset

    @property
    def asset(self) -> Union[Model, DataManager, DataSample, None]:
        if self.kind == AssetKind.ASSET_DATA_MANAGER:
            return self.data_manager
        elif self.kind == AssetKind.ASSET_DATA_SAMPLE:
            return self.data_sample
        elif self.kind == AssetKind.ASSET_MODEL:
            return self.model
        raise InvalidInputAsset(self.kind, AssetKind.ASSET_UNKNOWN)

    def __repr__(self) -> str:
        return f'ComputeTaskInputAsset(identifier="{self.identifier}",kind="{self.kind}",asset={self.asset})'


class ComputePlan(_Base):
    key: str
    tag: str
    cancelation_date: Optional[datetime.datetime]
    failure_date: Optional[datetime.datetime]

    @classmethod
    def from_grpc(cls, compute_plan: computeplan_pb2.ComputePlan) -> ComputePlan:
        cancelation_date = None
        if compute_plan.HasField("cancelation_date"):
            cancelation_date = compute_plan.cancelation_date.ToDatetime(tzinfo=datetime.timezone.utc)

        failure_date = None
        if compute_plan.HasField("failure_date"):
            failure_date = compute_plan.failure_date.ToDatetime(tzinfo=datetime.timezone.utc)

        return cls(
            key=compute_plan.key,
            tag=compute_plan.tag,
            cancelation_date=cancelation_date,
            failure_date=failure_date,
        )

    @property
    def is_runnable(self) -> bool:
        return self.cancelation_date is None and self.failure_date is None


class InvalidInputAsset(Exception):
    """InvalidInputAsset may be raised when manipulating a ComputeTaskInputAsset assuming a wrong AssetKind."""

    def __init__(self, actual: AssetKind, expected: AssetKind):
        message = f"Invalid asset kind, expected {expected} but have {actual}"
        super().__init__(message)


class OrchestratorVersion(pydantic.BaseModel):
    server: str
    chaincode: str

    @classmethod
    def from_grpc(cls, orc_version: info_pb2.QueryVersionResponse) -> OrchestratorVersion:
        return cls(server=orc_version.orchestrator, chaincode=orc_version.chaincode)
