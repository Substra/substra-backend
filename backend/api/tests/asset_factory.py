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
...     metric,
...     data_manager=data_manager,
...     data_samples=[data_sample],
...     parent_tasks=[train_task.key],
...     category=ComputeTask.Category.TASK_TEST,
...     status=ComputeTask.Status.STATUS_DONE,
... )
>>> performance = create_performance(test_task, metric)

Customized example:

>>> algo_data = create_algo_data()
>>> algo = create_algo(
...     key=algo_data.key,
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

from django.core import files
from django.utils import timezone

from api.models import Algo
from api.models import AlgoInput
from api.models import AlgoOutput
from api.models import ComputePlan
from api.models import ComputeTask
from api.models import ComputeTaskInput
from api.models import ComputeTaskOutput
from api.models import ComputeTaskOutputAsset
from api.models import DataManager
from api.models import DataSample
from api.models import Model
from api.models import Performance
from api.models import ProfilingStep
from api.models import TaskProfiling
from api.models.computetask import TaskDataSamples
from substrapp.models import Algo as AlgoData
from substrapp.models import ComputeTaskFailureReport as ComputeTaskLogs
from substrapp.models import DataManager as DataManagerData
from substrapp.models import DataSample as DataSampleData
from substrapp.models import Model as ModelData
from substrapp.tests import common
from substrapp.utils import get_hash

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_WORKER = "MyOrg1MSP"
DEFAULT_CHANNEL = "mychannel"
DUMMY_CHECKSUM = "dummy-checksum"
INPUT_ASSET_KEY = "5f23ae53-6541-45c1-ba78-fdfc56c51a52"


ALGO_INPUTS_PER_CATEGORY = common.ALGO_INPUTS_PER_CATEGORY_DICT
ALGO_OUTPUTS_PER_CATEGORY = common.ALGO_OUTPUTS_PER_CATEGORY_DICT


TASK_CATEGORY_TO_ALGO_CATEGORY = {
    ComputeTask.Category.TASK_TRAIN: Algo.Category.ALGO_SIMPLE,
    ComputeTask.Category.TASK_COMPOSITE: Algo.Category.ALGO_COMPOSITE,
    ComputeTask.Category.TASK_AGGREGATE: Algo.Category.ALGO_AGGREGATE,
    ComputeTask.Category.TASK_PREDICT: Algo.Category.ALGO_PREDICT,
    ComputeTask.Category.TASK_TEST: Algo.Category.ALGO_METRIC,
}


def get_storage_address(asset_kind: str, key: str, field: str) -> str:
    return f"http://testserver/{asset_kind}/{key}/{field}/"


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
    key: uuid.UUID = None,
    category: int = ComputeTask.Category.TASK_TRAIN,
    status: int = ComputeTask.Status.STATUS_TODO,
    rank: int = 1,
    worker: str = DEFAULT_WORKER,
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
        **get_log_permissions(owner, public),
    )
    if data_samples:
        for order, data_sample in enumerate(data_samples):
            TaskDataSamples.objects.create(compute_task_id=key, data_sample_id=data_sample, order=order)
        compute_task.refresh_from_db()

    for position, input in enumerate(compute_task.algo.inputs.all().order_by("identifier")):
        ComputeTaskInput.objects.create(
            task=compute_task,
            identifier=input.identifier,
            asset_key=INPUT_ASSET_KEY,
            position=position,
        )

    for output in compute_task.algo.outputs.all().order_by("identifier"):
        ComputeTaskOutput.objects.create(
            task=compute_task,
            identifier=output.identifier,
            permissions_download_public=public,
            permissions_download_authorized_ids=[owner],
            permissions_process_public=public,
            permissions_process_authorized_ids=[owner],
        )

    return compute_task


def create_model(
    compute_task: ComputeTask,
    key: uuid.UUID = None,
    category: int = Model.Category.MODEL_SIMPLE,
    identifier: str = "model",
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> Model:
    if key is None:
        key = uuid.uuid4()
    model = Model.objects.create(
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
    ComputeTaskOutputAsset.objects.create(
        task_output=compute_task.outputs.get(identifier=identifier),
        asset_kind=ComputeTaskOutputAsset.Kind.ASSET_MODEL,
        asset_key=model.key,
    )
    return model


def create_performance(
    compute_task: ComputeTask,
    metric: Algo,
    identifier: str = "performance",
    value: float = 1.0,
    channel: str = DEFAULT_CHANNEL,
) -> Performance:
    performance = Performance.objects.create(
        value=value,
        creation_date=timezone.now(),
        channel=channel,
        metric=metric,
        compute_task=compute_task,
    )
    ComputeTaskOutputAsset.objects.create(
        task_output=compute_task.outputs.get(identifier=identifier),
        asset_kind=ComputeTaskOutputAsset.Kind.ASSET_PERFORMANCE,
        asset_key=f"{compute_task.key}|{metric.key}",
    )
    return performance


def create_algo_data(
    key: uuid.UUID = None,
    file: files.File = None,
    description: files.File = None,
) -> AlgoData:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")
    if description is None:
        description = files.base.ContentFile("dummy content")

    algo_data = AlgoData.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    algo_data.file.save("algo", file)
    algo_data.description.save("description", description)
    return algo_data


def create_datamanager_data(
    key: uuid.UUID = None,
    name: str = "datamanager",
    opener: files.File = None,
    description: files.File = None,
) -> DataManagerData:
    if key is None:
        key = uuid.uuid4()
    if opener is None:
        opener = files.base.ContentFile("dummy content")
    if description is None:
        description = files.base.ContentFile("dummy content")

    data_manager_data = DataManagerData.objects.create(
        key=key,
        name=name,
        checksum=get_hash(opener),
    )
    data_manager_data.data_opener.save("opener", opener)
    data_manager_data.description.save("description", description)
    return data_manager_data


def create_datasample_data(
    key: uuid.UUID = None,
    file: files.File = None,
) -> DataSampleData:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")

    data_sample_data = DataSampleData.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    data_sample_data.file.save("datasample", file)
    return data_sample_data


def create_model_data(
    key: uuid.UUID = None,
    file: files.File = None,
) -> ModelData:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")

    model_data = ModelData.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    model_data.file.save("model", file)
    return model_data


def create_computetask_logs(
    compute_task_key: uuid.UUID,
    logs: files.File = None,
) -> ComputeTaskLogs:
    if logs is None:
        logs = files.base.ContentFile("dummy content")

    compute_task_logs = ComputeTaskLogs.objects.create(
        compute_task_key=compute_task_key,
        logs_checksum=get_hash(logs),
        creation_date=timezone.now(),
    )
    compute_task_logs.logs.save("logs", logs)
    return compute_task_logs


def create_computetask_profiling(compute_task: ComputeTask) -> TaskProfiling:
    profile = TaskProfiling.objects.create(compute_task=compute_task)
    ProfilingStep.objects.create(
        compute_task_profile=profile, step="step 1", duration=str(datetime.timedelta(seconds=10))
    )
    return profile
