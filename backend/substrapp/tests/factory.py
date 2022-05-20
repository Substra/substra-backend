"""
Utility module to create fixtures.

Basic example:

>>> algo = create_algo(category=Algo.Category.ALGO_SIMPLE)
>>> data_manager = create_datamanager()
>>> data_sample = create_datasample([data_manager])
>>> compute_plan = create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)

>>> train_task = create_computetask(
...     compute_plan,
...     algo,
...     data_manager=data_manager,
...     data_samples=[data_sample.key],
...     category=ComputeTask.Category.TASK_TRAIN,
...     status=ComputeTask.Status.STATUS_DONE,
... )
>>> model = create_model(train_task, category=Model.Category.MODEL_SIMPLE)

>>> metric = create_algo(category=Algo.Category.ALGO_METRIC)
>>> test_task = create_computetask(
...     compute_plan,
...     algo,
...     metrics=[metric],
...     data_manager=data_manager,
...     data_samples=[data_sample],
...     parent_tasks=[train_task.key],
...     category=ComputeTask.Category.TASK_TEST,
...     status=ComputeTask.Status.STATUS_DONE,
... )
>>> performance = create_performance(test_task, metric)

Customized example:

>>> algo_file = substrapp.models.Algo(...)
>>> algo = create_algo(
...     key=algo_file.key,
...     name="Random forest",
...     category=Algo.Category.ALGO_SIMPLE,
...     metadata={"foo": "bar"},
...     owner="MyOrg2MSP",
...     channel="yourchannel",
...     public="False",
... )
"""

import datetime
import uuid

from django.utils import timezone

from localrep.models import Algo
from localrep.models import AlgoInput
from localrep.models import AlgoOutput
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import DataManager
from localrep.models import DataSample
from localrep.models import Model
from localrep.models import Performance
from localrep.models.computetask import TaskDataSamples

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_CHANNEL = "mychannel"
DUMMY_CHECKSUM = "dummy-checksum"


# This logic belongs to the SDK but we replicate the mapping to generate realistic assets
ALGO_INPUTS_PER_CATEGORY = {
    "ALGO_SIMPLE": {
        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "multiple": True, "optional": False},
        "model": {"kind": "ASSET_MODEL", "multiple": False, "optional": True},
        "opener": {"kind": "ASSET_DATA_MANAGER", "multiple": False, "optional": False},
    },
    "ALGO_AGGREGATE": {
        "model": {"kind": "ASSET_MODEL", "multiple": True, "optional": False},
    },
    "ALGO_COMPOSITE": {
        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "multiple": True, "optional": False},
        "local": {"kind": "ASSET_MODEL", "multiple": False, "optional": True},
        "opener": {"kind": "ASSET_DATA_MANAGER", "multiple": False, "optional": False},
        "shared": {"kind": "ASSET_MODEL", "multiple": False, "optional": True},
    },
    "ALGO_METRIC": {
        "datasamples": {"kind": "ASSET_DATA_SAMPLE", "multiple": True, "optional": False},
        "opener": {"kind": "ASSET_DATA_MANAGER", "multiple": False, "optional": False},
        "predictions": {"kind": "ASSET_MODEL", "multiple": False, "optional": False},
    },
}


ALGO_OUTPUTS_PER_CATEGORY = {
    "ALGO_SIMPLE": {
        "model": {"kind": "ASSET_MODEL", "multiple": False},
    },
    "ALGO_AGGREGATE": {
        "model": {"kind": "ASSET_MODEL", "multiple": False},
    },
    "ALGO_COMPOSITE": {
        "local": {"kind": "ASSET_MODEL", "multiple": False},
        "shared": {"kind": "ASSET_MODEL", "multiple": False},
    },
    "ALGO_METRIC": {
        "performance": {"kind": "ASSET_PERFORMANCE", "multiple": False},
    },
}


def get_storage_address(asset: str, key: str, field: str) -> str:
    return f"http://testserver/{asset}/{key}/{field}/"


def get_permissions(owner: str, public: bool) -> dict:
    return {
        "permissions_download_public": public,
        "permissions_download_authorized_ids": [owner],
        "permissions_process_public": public,
        "permissions_process_authorized_ids": [owner],
    }


def get_log_permissions(owner: str, public: bool) -> dict:
    return {
        "logs_permission_public": public,
        "logs_permission_authorized_ids": [owner],
    }


def get_computetask_permissions(category: int, owner: str, public: bool) -> dict:
    if category in (ComputeTask.Category.TASK_TRAIN, ComputeTask.Category.TASK_AGGREGATE):
        return {
            "model_permissions_download_public": public,
            "model_permissions_download_authorized_ids": [owner],
            "model_permissions_process_public": public,
            "model_permissions_process_authorized_ids": [owner],
        }
    elif category == ComputeTask.Category.TASK_COMPOSITE:
        return {
            "head_permissions_download_public": public,
            "head_permissions_download_authorized_ids": [owner],
            "head_permissions_process_public": public,
            "head_permissions_process_authorized_ids": [owner],
            "trunk_permissions_download_public": public,
            "trunk_permissions_download_authorized_ids": [owner],
            "trunk_permissions_process_public": public,
            "trunk_permissions_process_authorized_ids": [owner],
        }
    else:  # ComputeTask.Category.TASK_TEST
        return {}


def get_computetask_dates(status: int, creation_date: datetime.datetime) -> tuple[datetime, datetime]:
    start_date = end_date = None
    if status in (
        ComputeTask.Status.STATUS_DOING,
        ComputeTask.Status.STATUS_DONE,
        ComputeTask.Status.STATUS_FAILED,
        ComputeTask.Status.STATUS_CANCELED,
    ):
        start_date = creation_date + datetime.timedelta(hours=1)
    if status in (
        ComputeTask.Status.STATUS_DONE,
        ComputeTask.Status.STATUS_FAILED,
        ComputeTask.Status.STATUS_CANCELED,
    ):
        end_date = creation_date + datetime.timedelta(hours=2)
    return start_date, end_date


def get_computeplan_dates(status: int, creation_date: datetime.datetime) -> tuple[datetime, datetime]:
    start_date = end_date = None
    if status in (
        ComputePlan.Status.PLAN_STATUS_DOING,
        ComputePlan.Status.PLAN_STATUS_DONE,
        ComputePlan.Status.PLAN_STATUS_FAILED,
        ComputePlan.Status.PLAN_STATUS_CANCELED,
    ):
        start_date = creation_date + datetime.timedelta(hours=1)
    if status in (
        ComputePlan.Status.PLAN_STATUS_DONE,
        ComputePlan.Status.PLAN_STATUS_FAILED,
        ComputePlan.Status.PLAN_STATUS_CANCELED,
    ):
        end_date = creation_date + datetime.timedelta(hours=2)
    return start_date, end_date


def create_algo(
    key: uuid.UUID = None,
    name: str = "algo",
    category: int = Algo.Category.ALGO_SIMPLE,
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> Algo:
    if key is None:
        key = uuid.uuid4()

    algo = Algo.objects.create(
        key=key,
        name=name,
        category=category,
        metadata=metadata or {},
        algorithm_address=get_storage_address("algo", key, "file"),
        algorithm_checksum=DUMMY_CHECKSUM,
        description_address=get_storage_address("algo", key, "description"),
        description_checksum=DUMMY_CHECKSUM,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
    )

    for identifier, algo_input in ALGO_INPUTS_PER_CATEGORY[category].items():
        AlgoInput.objects.create(algo=algo, identifier=identifier, **algo_input)
    for identifier, algo_output in ALGO_OUTPUTS_PER_CATEGORY[category].items():
        AlgoOutput.objects.create(algo=algo, identifier=identifier, **algo_output)

    return algo


def create_datamanager(
    key: uuid.UUID = None,
    name: str = "datamanager",
    type: str = "Test",
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> DataManager:
    if key is None:
        key = uuid.uuid4()
    return DataManager.objects.create(
        key=key,
        name=name,
        type=type,
        metadata=metadata or {},
        opener_address=get_storage_address("data_manager", key, "opener"),
        opener_checksum=DUMMY_CHECKSUM,
        description_address=get_storage_address("data_manager", key, "description"),
        description_checksum=DUMMY_CHECKSUM,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
        **get_log_permissions(owner, public),
    )


def create_datasample(
    data_managers: list[DataManager],
    key: uuid.UUID = None,
    test_only: bool = False,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
) -> DataSample:
    if key is None:
        key = uuid.uuid4()
    data_sample = DataSample.objects.create(
        key=key,
        test_only=test_only,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
    )
    data_sample.data_managers.set(data_managers)
    data_sample.save()
    return data_sample


def create_computeplan(
    key: uuid.UUID = None,
    status: int = ComputePlan.Status.PLAN_STATUS_TODO,
    tag: str = "",
    name: str = "computeplan",
    delete_intermediary_models: bool = False,
    failed_task_key: str = None,
    failed_task_category: int = None,
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
) -> ComputePlan:
    creation_date = timezone.now()
    start_date, end_date = get_computeplan_dates(status, creation_date)
    if key is None:
        key = uuid.uuid4()
    return ComputePlan.objects.create(
        key=key,
        status=status,
        tag=tag,
        name=name,
        delete_intermediary_models=delete_intermediary_models,
        start_date=start_date,
        end_date=end_date,
        failed_task_key=failed_task_key,
        failed_task_category=failed_task_category,
        metadata=metadata or {},
        creation_date=creation_date,
        owner=owner,
        channel=channel,
    )


def create_computetask(
    compute_plan: ComputePlan,
    algo: Algo,
    parent_tasks: list[uuid.UUID] = None,
    data_manager: DataManager = None,
    data_samples: list[uuid.UUID] = None,
    metrics: list[Algo] = None,
    key: uuid.UUID = None,
    category: int = ComputeTask.Category.TASK_TRAIN,
    status: int = ComputeTask.Status.STATUS_TODO,
    rank: int = 1,
    worker: str = DEFAULT_OWNER,
    tag: str = "",
    error_type: int = None,
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> ComputeTask:
    creation_date = timezone.now()
    start_date, end_date = get_computetask_dates(status, creation_date)
    if key is None:
        key = uuid.uuid4()
    compute_task = ComputeTask.objects.create(
        compute_plan=compute_plan,
        algo=algo,
        parent_tasks=parent_tasks or [],
        data_manager=data_manager,
        key=key,
        category=category,
        status=status,
        rank=rank,
        worker=worker,
        tag=tag,
        start_date=start_date,
        end_date=end_date,
        error_type=error_type,
        metadata=metadata or {},
        logs_address=get_storage_address("logs", key, "file"),
        logs_checksum=DUMMY_CHECKSUM,
        logs_owner=owner,
        creation_date=creation_date,
        owner=owner,
        channel=channel,
        **get_computetask_permissions(category, owner, public),
        **get_log_permissions(owner, public),
    )
    if metrics:
        compute_task.metrics.set(metrics)
        compute_task.save()
    if data_samples:
        for order, data_sample in enumerate(data_samples):
            TaskDataSamples.objects.create(compute_task_id=key, data_sample_id=data_sample, order=order)
        compute_task.refresh_from_db()

    return compute_task


def create_model(
    compute_task: ComputeTask,
    key: uuid.UUID = None,
    category: int = Model.Category.MODEL_SIMPLE,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> Model:
    if key is None:
        key = uuid.uuid4()
    return Model.objects.create(
        compute_task=compute_task,
        key=key,
        category=category,
        model_address=get_storage_address("model", key, "file"),
        model_checksum=DUMMY_CHECKSUM,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
    )


def create_performance(
    compute_task: ComputeTask,
    metric: Algo,
    value: float = 1.0,
    channel: str = DEFAULT_CHANNEL,
) -> Performance:
    return Performance.objects.create(
        value=value,
        creation_date=timezone.now(),
        channel=channel,
        metric=metric,
        compute_task=compute_task,
    )
