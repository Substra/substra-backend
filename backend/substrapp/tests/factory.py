"""
Utility module to create fixtures.

Basic example:

>>> algo = create_algo(category=algo_pb2.ALGO_SIMPLE)
>>> data_manager = create_datamanager()
>>> data_sample = create_datasample([data_manager])
>>> compute_plan = create_computeplan(status=computeplan_pb2.PLAN_STATUS_DONE)

>>> train_task = create_computetask(
...     compute_plan,
...     algo,
...     data_manager=data_manager,
...     data_samples=[data_sample.key],
...     category=computetask_pb2.TASK_TRAIN,
...     status=computetask_pb2.STATUS_DONE,
... )
>>> model = create_model(train_task, category=model_pb2.MODEL_SIMPLE)

>>> metric = create_metric()
>>> test_task = create_computetask(
...     compute_plan,
...     algo,
...     metrics=[metric],
...     data_manager=data_manager,
...     data_samples=[data_sample.key],
...     parent_tasks=[train_task.key],
...     category=computetask_pb2.TASK_TEST,
...     status=computetask_pb2.STATUS_DONE,
... )
>>> performance = create_performance(test_task, metric)

Customized example:

>>> algo_file = substrapp.models.Algo(...)
>>> algo = create_algo(
...     key=algo_file.key,
...     name="Random forest",
...     category=algo_pb2.ALGO_SIMPLE,
...     metadata={"foo": "bar"},
...     owner="MyOrg2MSP",
...     channel="yourchannel",
...     public="False",
... )
"""

import datetime
import uuid

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.model_pb2 as model_pb2
from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import DataManager
from localrep.models import DataSample
from localrep.models import Metric
from localrep.models import Model
from localrep.models import Performance

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_CHANNEL = "mychannel"
DUMMY_CHECKSUM = "dummy-checksum"


def get_storage_address(asset: str, key: str, field: str):
    return f"http://testserver/{asset}/{key}/{field}/"


def get_permissions(owner: str, public: bool):
    return {
        "permissions_download_public": public,
        "permissions_download_authorized_ids": [owner],
        "permissions_process_public": public,
        "permissions_process_authorized_ids": [owner],
    }


def get_computetask_permissions(status: int, owner: str, public: bool):
    if status in (computetask_pb2.TASK_TRAIN, computetask_pb2.TASK_AGGREGATE):
        return {
            "model_permissions_download_public": public,
            "model_permissions_download_authorized_ids": [owner],
            "model_permissions_process_public": public,
            "model_permissions_process_authorized_ids": [owner],
        }
    elif status == computetask_pb2.TASK_COMPOSITE:
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
    else:  # computetask_pb2.TASK_TEST
        return {}


def get_computetask_dates(status: int, creation_date: datetime.datetime) -> tuple[datetime, datetime]:
    start_date = end_date = None
    if status in (
        computetask_pb2.STATUS_DOING,
        computetask_pb2.STATUS_DONE,
        computetask_pb2.STATUS_FAILED,
        computetask_pb2.STATUS_CANCELED,
    ):
        start_date = creation_date + datetime.timedelta(hours=1)
    if status in (
        computetask_pb2.STATUS_DONE,
        computetask_pb2.STATUS_FAILED,
        computetask_pb2.STATUS_CANCELED,
    ):
        end_date = creation_date + datetime.timedelta(hours=2)
    return start_date, end_date


def get_computeplan_dates(status: int, creation_date: datetime.datetime) -> tuple[datetime, datetime]:
    start_date = end_date = None
    if status in (
        computeplan_pb2.PLAN_STATUS_DOING,
        computeplan_pb2.PLAN_STATUS_DONE,
        computeplan_pb2.PLAN_STATUS_FAILED,
        computeplan_pb2.PLAN_STATUS_CANCELED,
    ):
        start_date = creation_date + datetime.timedelta(days=1)
    if status in (
        computeplan_pb2.PLAN_STATUS_DONE,
        computeplan_pb2.PLAN_STATUS_FAILED,
        computeplan_pb2.PLAN_STATUS_CANCELED,
    ):
        end_date = creation_date + datetime.timedelta(days=2)
    return start_date, end_date


def create_algo(
    key: uuid.UUID = None,
    name: str = "algo",
    category: int = algo_pb2.ALGO_SIMPLE,
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = True,
) -> Algo:
    if key is None:
        key = uuid.uuid4()
    return Algo.objects.create(
        key=key,
        name=name,
        category=category,
        metadata=metadata or {},
        algorithm_address=get_storage_address("algo", key, "file"),
        algorithm_checksum=DUMMY_CHECKSUM,
        description_address=get_storage_address("algo", key, "description"),
        description_checksum=DUMMY_CHECKSUM,
        creation_date=datetime.datetime.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
    )


def create_metric(
    key: uuid.UUID = None,
    name: str = "metric",
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = True,
) -> Metric:
    if key is None:
        key = uuid.uuid4()
    return Metric.objects.create(
        key=key,
        name=name,
        metadata=metadata or {},
        metric_address=get_storage_address("metric", key, "metrics"),
        metric_checksum=DUMMY_CHECKSUM,
        description_address=get_storage_address("metric", key, "description"),
        description_checksum=DUMMY_CHECKSUM,
        owner=owner,
        creation_date=datetime.datetime.now(),
        channel=channel,
        **get_permissions(owner, public),
    )


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
        logs_permission_public=True,
        logs_permission_authorized_ids=[owner],
        creation_date=datetime.datetime.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
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
        creation_date=datetime.datetime.now(),
        owner=owner,
        channel=channel,
    )
    data_sample.data_managers.set(data_managers)
    data_sample.save()
    return data_sample


def create_computeplan(
    key: uuid.UUID = None,
    status: int = computeplan_pb2.PLAN_STATUS_TODO,
    tag: str = "",
    delete_intermediary_models: bool = False,
    failed_task_key: str = None,
    failed_task_category: int = None,
    metadata: dict = None,
    channel: str = DEFAULT_CHANNEL,
) -> ComputePlan:
    creation_date = datetime.datetime.now()
    start_date, end_date = get_computeplan_dates(status, creation_date)
    if key is None:
        key = uuid.uuid4()
    return ComputePlan.objects.create(
        key=key,
        status=status,
        tag=tag,
        delete_intermediary_models=delete_intermediary_models,
        start_date=start_date,
        end_date=end_date,
        failed_task_key=failed_task_key,
        failed_task_category=failed_task_category,
        metadata=metadata or {},
        creation_date=creation_date,
        channel=channel,
    )


def create_computetask(
    compute_plan: ComputePlan,
    algo: Algo,
    parent_tasks: list[uuid.UUID] = None,
    data_manager: DataManager = None,
    data_samples: list[uuid.UUID] = None,
    metrics: list[Metric] = None,
    key: uuid.UUID = None,
    category: int = computetask_pb2.TASK_TRAIN,
    status: int = computetask_pb2.STATUS_TODO,
    rank: int = 1,
    worker: str = DEFAULT_OWNER,
    tag: str = "",
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> ComputeTask:
    creation_date = datetime.datetime.now()
    start_date, end_date = get_computetask_dates(status, creation_date)
    if key is None:
        key = uuid.uuid4()
    compute_task = ComputeTask.objects.create(
        compute_plan=compute_plan,
        algo=algo,
        parent_tasks=parent_tasks,
        data_manager=data_manager,
        data_samples=data_samples,
        key=key,
        category=category,
        status=status,
        rank=rank,
        worker=worker,
        tag=tag,
        start_date=start_date,
        end_date=end_date,
        metadata=metadata or {},
        logs_address=get_storage_address("logs", key, "file"),
        logs_checksum=DUMMY_CHECKSUM,
        logs_permission_public=True,
        logs_permission_authorized_ids=[owner],
        creation_date=creation_date,
        owner=owner,
        channel=channel,
        **get_computetask_permissions(status, owner, public),
    )
    if metrics:
        compute_task.metrics.set(metrics)
        compute_task.save()
    return compute_task


def create_model(
    compute_task: ComputeTask,
    key: uuid.UUID = None,
    category: int = model_pb2.MODEL_SIMPLE,
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
        creation_date=datetime.datetime.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
    )


def create_performance(
    compute_task: ComputeTask,
    metric: Metric,
    value: float = "1.0",
    channel: str = DEFAULT_CHANNEL,
) -> Performance:
    return Performance.objects.create(
        value=value,
        creation_date=datetime.datetime.now(),
        channel=channel,
        metric=metric,
        compute_task=compute_task,
    )
