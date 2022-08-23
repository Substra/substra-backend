from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Union

import orchestrator.common_pb2 as common_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.model_pb2 as model_pb2
from orchestrator import datamanager_pb2
from orchestrator import datasample_pb2


class AssetKind(Enum):
    ASSET_UNKNOWN = 0
    ASSET_ORGANIZATION = 1
    ASSET_DATA_SAMPLE = 3
    ASSET_DATA_MANAGER = 4
    ASSET_ALGO = 5
    ASSET_COMPUTE_TASK = 6
    ASSET_COMPUTE_PLAN = 7
    ASSET_MODEL = 8
    ASSET_PERFORMANCE = 9
    ASSET_FAILURE_REPORT = 10
    ASSET_COMPUTE_TASK_OUTPUT_ASSET = 11


@dataclass
class Address:
    uri: str
    checksum: str

    @classmethod
    def from_grpc(cls, a: common_pb2.Addressable) -> "Address":
        return cls(
            uri=a.storage_address,
            checksum=a.checksum,
        )


@dataclass
class Model:
    """Model is a partial representation of an orchestrator Model

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str
    compute_task_key: str
    address: Address

    @classmethod
    def from_grpc(cls, m: model_pb2.Model) -> "Model":
        """Creates a Model from grpc message"""
        return cls(
            key=m.key,
            compute_task_key=m.compute_task_key,
            address=Address.from_grpc(m.address),
        )


@dataclass
class DataSample:
    """DataSamples is a partial representation of an orchestrator DataSample

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str

    @classmethod
    def from_grpc(cls, s: datasample_pb2.DataSample) -> "DataSample":
        """Creates a DataSample from grpc message"""
        return cls(
            key=s.key,
        )


@dataclass
class DataManager:
    """DataManager is a partial representation of an orchestrator DataManager

    Partial because I didn't have the need and bandwidth to deal with all attributes.
    Supporting new ones should be trivial though.
    """

    key: str
    opener: Address

    @classmethod
    def from_grpc(cls, m: datamanager_pb2.DataManager) -> "DataManager":
        """Creates a DataManager from grpc message"""
        return cls(key=m.key, opener=Address.from_grpc(m.opener))


class ComputeTaskInputAsset:
    _identifier: str
    _kind: AssetKind = AssetKind.ASSET_UNKNOWN
    _model: Optional[Model] = None
    _data_manager: Optional[DataManager] = None
    _data_sample: Optional[DataSample] = None

    def __init__(self, input_asset: computetask_pb2.ComputeTaskInputAsset) -> "ComputeTaskInputAsset":
        self._identifier = input_asset.identifier
        if input_asset.WhichOneof("asset") == "data_manager":
            self._kind = AssetKind.ASSET_DATA_MANAGER
            self._data_manager = DataManager.from_grpc(input_asset.data_manager)
        elif input_asset.WhichOneof("asset") == "data_sample":
            self._kind = AssetKind.ASSET_DATA_SAMPLE
            self._data_sample = DataSample.from_grpc(input_asset.data_sample)
        elif input_asset.WhichOneof("asset") == "model":
            self._kind = AssetKind.ASSET_MODEL
            self._model = Model.from_grpc(input_asset.model)

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def kind(self) -> AssetKind:
        return self._kind

    @property
    def model(self) -> Model:
        if not self._model:
            raise InvalidInputAsset(self._kind, AssetKind.ASSET_MODEL)
        return self._model

    @property
    def data_sample(self) -> DataSample:
        if not self._data_sample:
            raise InvalidInputAsset(self._kind, AssetKind.ASSET_DATA_SAMPLE)
        return self._data_sample

    @property
    def data_manager(self) -> DataManager:
        if not self._data_manager:
            raise InvalidInputAsset(self._kind, AssetKind.ASSET_DATA_MANAGER)
        return self._data_manager

    @property
    def asset(self) -> Union[Model, DataManager, DataSample]:
        if self._kind == AssetKind.ASSET_DATA_MANAGER:
            return self._data_manager
        elif self._kind == AssetKind.ASSET_DATA_SAMPLE:
            return self._data_sample
        elif self._kind == AssetKind.ASSET_MODEL:
            return self._model
        raise InvalidInputAsset(self._kind, AssetKind.ASSET_UNKNOWN)

    def __repr__(self) -> str:
        return f'ComputeTaskInputAsset(identifier="{self._identifier}",kind="{self._kind}",asset={self.asset})'


class InvalidInputAsset(Exception):
    """InvalidInputAsset may be raised when manipulating a ComputeTaskInputAsset assuming a wrong AssetKind."""

    def __init__(self, actual: AssetKind, expected: AssetKind):
        message = f"Invalid asset kind, expected {expected} but have {actual}"
        super().__init__(message)
