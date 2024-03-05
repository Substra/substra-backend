"""
Utility module to create fixtures.

Basic example:

>>> function = create_function(
...     inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
...     outputs=factory.build_function_outputs(["model"]),
... )
>>> data_manager = create_datamanager()
>>> data_sample = create_datasample([data_manager])
>>> compute_plan = create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)

>>> train_task = create_computetask(
...     compute_plan,
...     function,
...     inputs=factory.build_computetask_inputs(
...         function,
...         {
...             "opener": [data_manager.key],
...             "datasamples": [data_sample.key],
...         },
...     ),
...     outputs=factory.build_computetask_outputs(function),
...     status=ComputeTask.Status.STATUS_DONE,
... )
>>> model = create_model(train_task, identifier="model")

>>> metric = create_function(
...     inputs=factory.build_function_inputs(["datasamples", "opener", "model"]),
...     outputs=factory.build_function_outputs(["performance"]),
... )
>>> test_task = create_computetask(
...     compute_plan,
...     metric,
...     inputs=factory.build_computetask_inputs(
...         metric,
...         {
...             "opener": [data_manager.key],
...             "datasamples": [data_sample.key],
...             "model": [train_task.key],
...         },
...     ),
...     outputs=factory.build_computetask_outputs(metric),
...     status=ComputeTask.Status.STATUS_DONE,
... )
>>> performance = create_performance(test_task.outputs[0])

Customized example:

>>> function_data = create_function_files()
>>> function = create_function(
...     key=function_data.key,
...     name="Random forest",
...     category=FunctionCategory.simple,
...     metadata={"foo": "bar"},
...     owner="MyOrg2MSP",
...     channel="yourchannel",
...     public="False",
... )
"""

import datetime
import uuid
from typing import Optional

from django.core import files
from django.utils import timezone

from api.models import ComputePlan
from api.models import ComputeTask
from api.models import ComputeTaskInput
from api.models import ComputeTaskInputAsset
from api.models import ComputeTaskOutput
from api.models import ComputeTaskOutputAsset
from api.models import DataManager
from api.models import DataSample
from api.models import Function
from api.models import FunctionInput
from api.models import FunctionOutput
from api.models import Model
from api.models import Performance
from api.models import TaskProfiling
from substrapp.models import AssetFailureReport
from substrapp.models import DataManager as DataManagerFiles
from substrapp.models import DataSample as DataSampleFiles
from substrapp.models import FailedAssetKind
from substrapp.models import Function as FunctionFiles
from substrapp.models import Model as ModelFiles
from substrapp.utils import get_hash

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_WORKER = "MyOrg1MSP"
DEFAULT_CHANNEL = "mychannel"
DUMMY_CHECKSUM = "dummy-checksum"


# Inputs and outputs values belongs to the business logic and are handled at the substra SDK level.
# We use them here only to have realistic test data, but the API should remained agnostic from them.

FUNCTION_INPUTS = {
    "datasamples": dict(kind=FunctionInput.Kind.ASSET_DATA_SAMPLE, multiple=True, optional=False),
    "opener": dict(kind=FunctionInput.Kind.ASSET_DATA_MANAGER, multiple=False, optional=False),
    "model": dict(kind=FunctionInput.Kind.ASSET_MODEL, multiple=False, optional=True),
    "models": dict(kind=FunctionInput.Kind.ASSET_MODEL, multiple=True, optional=True),
    "local": dict(kind=FunctionInput.Kind.ASSET_MODEL, multiple=False, optional=True),
    "shared": dict(kind=FunctionInput.Kind.ASSET_MODEL, multiple=False, optional=True),
    "predictions": dict(kind=FunctionInput.Kind.ASSET_MODEL, multiple=False, optional=False),
}
FUNCTION_OUTPUTS = {
    "model": dict(kind=FunctionOutput.Kind.ASSET_MODEL, multiple=False),
    "local": dict(kind=FunctionOutput.Kind.ASSET_MODEL, multiple=False),
    "shared": dict(kind=FunctionOutput.Kind.ASSET_MODEL, multiple=False),
    "predictions": dict(kind=FunctionOutput.Kind.ASSET_MODEL, multiple=False),
    "performance": dict(kind=FunctionOutput.Kind.ASSET_PERFORMANCE, multiple=False),
}


def build_function_inputs(identifiers: list[str]) -> list[FunctionInput]:
    return [FunctionInput(identifier=identifier, **FUNCTION_INPUTS[identifier]) for identifier in identifiers]


def build_function_outputs(identifiers: list[str]) -> list[FunctionOutput]:
    return [FunctionOutput(identifier=identifier, **FUNCTION_OUTPUTS[identifier]) for identifier in identifiers]


def build_computetask_inputs(
    function: Function,
    keys: dict[str : list[uuid.UUID]],
) -> list[ComputeTaskInput]:
    task_inputs = []
    for function_input in function.inputs.all():
        for key in keys.get(function_input.identifier, []):
            task_input = ComputeTaskInput(identifier=function_input.identifier)
            if function_input.kind in (FunctionInput.Kind.ASSET_DATA_MANAGER, FunctionInput.Kind.ASSET_DATA_SAMPLE):
                task_input.asset_key = key
            else:  # we assume that all other assets are produced by parent tasks
                task_input.parent_task_key_id = key
                task_input.parent_task_output_identifier = function_input.identifier
            task_inputs.append(task_input)
    return task_inputs


def build_computetask_outputs(
    function: Function,
    owner: str = DEFAULT_OWNER,
    public: bool = False,
) -> list[ComputeTaskOutput]:
    return [
        ComputeTaskOutput(
            identifier=function_output.identifier,
            permissions_download_public=public,
            permissions_download_authorized_ids=[owner],
            permissions_process_public=public,
            permissions_process_authorized_ids=[owner],
        )
        for function_output in function.outputs.all()
    ]


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
        ComputeTask.Status.STATUS_BUILDING,
        ComputeTask.Status.STATUS_WAITING_FOR_PARENT_TASKS,
        ComputeTask.Status.STATUS_WAITING_FOR_EXECUTOR_SLOT,
        ComputeTask.Status.STATUS_EXECUTING,
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


def create_function(
    inputs: list[FunctionInput] = None,
    outputs: list[FunctionOutput] = None,
    key: uuid.UUID = None,
    name: str = "function",
    metadata: dict = None,
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
    public: bool = False,
) -> Function:
    if key is None:
        key = uuid.uuid4()

    function = Function.objects.create(
        key=key,
        name=name,
        metadata=metadata or {},
        archive_address=get_storage_address("function", key, "file"),
        archive_checksum=DUMMY_CHECKSUM,
        description_address=get_storage_address("function", key, "description"),
        description_checksum=DUMMY_CHECKSUM,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
        status=Function.Status.FUNCTION_STATUS_WAITING,
        **get_permissions(owner, public),
    )

    if inputs:
        for function_input in inputs:
            function_input.function = function
            function_input.channel = channel
            function_input.save()
    if outputs:
        for function_output in outputs:
            function_output.function = function
            function_output.channel = channel
            function_output.save()

    return function


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
    owner: str = DEFAULT_OWNER,
    channel: str = DEFAULT_CHANNEL,
) -> DataSample:
    if key is None:
        key = uuid.uuid4()
    data_sample = DataSample.objects.create(
        key=key,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
    )
    data_sample.data_managers.set(data_managers)
    data_sample.save()
    return data_sample


def create_computeplan(
    key: uuid.UUID = None,
    status: int = ComputePlan.Status.PLAN_STATUS_CREATED,
    tag: str = "",
    name: str = "computeplan",
    failed_task_key: str = None,
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
        metadata=metadata or {},
        creation_date=creation_date,
        owner=owner,
        channel=channel,
    )


def create_computetask(
    compute_plan: ComputePlan,
    function: Function,
    inputs: list[ComputeTaskInput] = None,
    outputs: list[ComputeTaskOutput] = None,
    key: uuid.UUID = None,
    status: int = ComputeTask.Status.STATUS_WAITING_FOR_EXECUTOR_SLOT,
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
        function=function,
        key=key,
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

    if inputs:
        input_kinds = {
            function_input.identifier: function_input.kind for function_input in compute_task.function.inputs.all()
        }
        for position, task_input in enumerate(inputs):
            task_input.task = compute_task
            task_input.channel = channel
            task_input.position = position
            task_input.save()
            if task_input.asset_key:
                ComputeTaskInputAsset.objects.create(
                    task_input=task_input,
                    asset_kind=input_kinds[task_input.identifier],
                    asset_key=task_input.asset_key,
                    channel=channel,
                )

    if outputs:
        for task_output in outputs:
            task_output.task = compute_task
            task_output.channel = channel
            task_output.save()

    return compute_task


def create_model(
    compute_task: ComputeTask,
    key: uuid.UUID = None,
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
        model_address=get_storage_address("model", key, "file"),
        model_checksum=DUMMY_CHECKSUM,
        creation_date=timezone.now(),
        owner=owner,
        channel=channel,
        **get_permissions(owner, public),
    )
    ComputeTaskOutputAsset.objects.create(
        task_output=compute_task.outputs.get(identifier=identifier),
        asset_kind=FunctionOutput.Kind.ASSET_MODEL,
        asset_key=model.key,
        channel=channel,
    )
    for task_input in ComputeTaskInput.objects.filter(
        parent_task_key=compute_task,
        parent_task_output_identifier=identifier,
    ):
        ComputeTaskInputAsset.objects.create(
            task_input=task_input,
            asset_kind=FunctionOutput.Kind.ASSET_MODEL,
            asset_key=model.key,
            channel=channel,
        )
    return model


def create_performance(
    compute_task_output: ComputeTaskOutput,
    metric: Function,
    value: float = 1.0,
    channel: str = DEFAULT_CHANNEL,
) -> Performance:
    performance = Performance.objects.create(
        value=value,
        creation_date=timezone.now(),
        channel=channel,
        compute_task_output=compute_task_output,
    )
    ComputeTaskOutputAsset.objects.create(
        task_output=compute_task_output,
        asset_kind=FunctionOutput.Kind.ASSET_PERFORMANCE,
        asset_key=f"{compute_task_output.task.key}|{metric.key}",
        channel=channel,
    )
    return performance


def create_function_files(
    key: uuid.UUID = None,
    file: files.File = None,
    description: files.File = None,
) -> FunctionFiles:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")
    if description is None:
        description = files.base.ContentFile("dummy content")

    function_files = FunctionFiles.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    function_files.file.save("archive", file)
    function_files.description.save("description", description)
    return function_files


def create_datamanager_files(
    key: uuid.UUID = None,
    name: str = "datamanager",
    opener: files.File = None,
    description: files.File = None,
) -> DataManagerFiles:
    if key is None:
        key = uuid.uuid4()
    if opener is None:
        opener = files.base.ContentFile("dummy content")
    if description is None:
        description = files.base.ContentFile("dummy content")

    data_manager_files = DataManagerFiles.objects.create(
        key=key,
        name=name,
        checksum=get_hash(opener),
    )
    data_manager_files.data_opener.save("opener", opener)
    data_manager_files.description.save("description", description)
    return data_manager_files


def create_datasample_files(
    key: uuid.UUID = None,
    file: files.File = None,
) -> DataSampleFiles:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")

    data_sample_files = DataSampleFiles.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    data_sample_files.file.save("datasample", file)
    return data_sample_files


def create_model_files(
    key: uuid.UUID = None,
    file: files.File = None,
) -> ModelFiles:
    if key is None:
        key = uuid.uuid4()
    if file is None:
        file = files.base.ContentFile("dummy content")

    model_files = ModelFiles.objects.create(
        key=key,
        checksum=get_hash(file),
    )
    model_files.file.save("model", file)
    return model_files


def create_asset_logs(
    asset_key: uuid.UUID,
    asset_type: FailedAssetKind,
    logs: Optional[files.File] = None,
    owner: str = "",
) -> AssetFailureReport:
    if logs is None:
        logs = files.base.ContentFile("dummy content")

    asset_logs = AssetFailureReport.objects.create(
        asset_key=asset_key,
        asset_type=asset_type,
        logs_checksum=get_hash(logs),
        creation_date=timezone.now(),
        logs_address=get_storage_address("logs", asset_key, "file"),
        logs_owner=owner,
    )
    asset_logs.logs.save("logs", logs)
    return asset_logs


def create_computetask_logs(
    compute_task_key: uuid.UUID,
    logs: Optional[files.File] = None,
    owner: str = "",
) -> AssetFailureReport:
    return create_asset_logs(compute_task_key, FailedAssetKind.FAILED_ASSET_COMPUTE_TASK, logs, owner=owner)


def create_function_logs(
    function_key: uuid.UUID,
    logs: Optional[files.File] = None,
    owner: str = "",
) -> AssetFailureReport:
    return create_asset_logs(function_key, FailedAssetKind.FAILED_ASSET_FUNCTION, logs, owner=owner)


def create_computetask_profiling(compute_task: ComputeTask) -> TaskProfiling:
    profile = TaskProfiling.objects.create(compute_task=compute_task)
    return profile
