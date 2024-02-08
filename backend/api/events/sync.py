import secrets
import string
from typing import Optional

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from api.errors import AlreadyExistsError
from api.events.dynamic_fields import parse_computetask_dates_from_event
from api.models import ComputePlan
from api.models import ComputeTask
from api.models import ComputeTaskInput
from api.models import ComputeTaskInputAsset
from api.models import ComputeTaskOutput
from api.models import ComputeTaskOutputAsset
from api.models import DataManager
from api.models import DataSample
from api.models import Function
from api.models import Model
from api.serializers import ChannelOrganizationSerializer
from api.serializers import ComputePlanSerializer
from api.serializers import ComputeTaskSerializer
from api.serializers import DataManagerSerializer
from api.serializers import DataSampleSerializer
from api.serializers import FunctionSerializer
from api.serializers import ModelSerializer
from api.serializers import PerformanceSerializer
from orchestrator import client as orc_client
from orchestrator import computetask
from orchestrator import failure_report_pb2

logger = structlog.get_logger(__name__)


# dummy user to be referenced as creator for asset outside current organization
def _get_or_create_external_user() -> User:
    username = settings.VIRTUAL_USERNAMES["EXTERNAL"]
    user_external, created = User.objects.get_or_create(username=username, is_active=False)
    if created:
        password = "".join(
            (secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(24))
        )
        user_external.set_password(password)
        user_external.save()

    return user_external


def _on_create_organization_event(event: dict) -> None:
    """Process create organization event to update local database."""
    logger.debug("Syncing organization create", asset_key=event["asset_key"], event_id=event["id"])
    _create_organization(channel=event["channel"], data=event["organization"])


def _create_organization(channel: str, data: dict) -> None:
    data["channel"] = channel

    serializer = ChannelOrganizationSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Organization already exists", organization_id=data["id"], channel=data["channel"])


def _on_create_function_event(event: dict) -> None:
    """Process create function event to update local database."""
    logger.debug("Syncing function create", asset_key=event["asset_key"], event_id=event["id"])
    _create_function(channel=event["channel"], data=event["function"])


def _create_function(channel: str, data: dict) -> None:
    data["channel"] = channel
    serializer = FunctionSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Function already exists", asset_key=data["key"])


def _on_update_function_event(event: dict) -> None:
    """Process update function event to update local database."""
    logger.debug("Syncing function update", asset_key=event["asset_key"], event_id=event["id"])
    function = event["function"]
    _update_function(
        key=event["asset_key"],
        name=function["name"],
        status=function["status"],
        image_address=function["image"].get("storageAddress"),
        image_checksum=function["image"].get("checksum"),
    )


def _update_function(
    key: str,
    *,
    name: Optional[str] = None,
    status: Optional[str] = None,
    image_address: Optional[str] = None,
    image_checksum: Optional[str] = None,
) -> None:
    """Process update function event to update local database."""
    function = Function.objects.get(key=key)

    if name:
        function.name = name
    if status:
        function.status = status
    if image_address and image_checksum:
        function.image_address = image_address
        function.image_checksum = image_checksum
    function.save()


def _on_create_computeplan_event(event: dict) -> None:
    """Process create computeplan event to update local database."""
    logger.debug("Syncing computeplan", asset_key=event["asset_key"], event_id=event["id"])
    _create_computeplan(channel=event["channel"], data=event["compute_plan"])


def _create_computeplan(channel: str, data: dict) -> None:
    data["channel"] = channel

    # if event received, we assume compute plan was created by another organization
    creator = _get_or_create_external_user()
    data["creator"] = creator.id

    serializer = ComputePlanSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("ComputePlan already exists", asset_key=data["key"])


def _on_update_computeplan_event(event: dict) -> None:
    """Process update compute plan event to update local database."""
    logger.debug("Syncing compute plan update", asset_key=event["asset_key"], event_id=event["id"])
    _update_computeplan(key=event["asset_key"], data=event["compute_plan"])


def _update_computeplan(key: str, data: dict) -> None:
    """Process update compute plan event to update local database."""

    from api.models.computeplan import ComputePlan

    compute_plan = ComputePlan.objects.get(key=key)
    compute_plan.cancelation_date = data.get("cancelation_date")
    compute_plan.name = data.get("name")
    compute_plan.save()
    compute_plan.update_dates()
    compute_plan.update_status()


def _on_create_computetask_event(event: dict) -> None:
    """Process create computetask event to update local database."""
    logger.debug("Syncing computetask create", asset_key=event["asset_key"], event_id=event["id"])

    task_data = event["compute_task"]
    _create_computetask(channel=event["channel"], data=task_data)

    compute_plan = ComputePlan.objects.get(key=task_data["compute_plan_key"])
    compute_plan.update_dates()
    compute_plan.update_status()


def _create_computetask(
    channel: str, data: dict, start_date: str = None, end_date: str = None, failure_report: dict = None
) -> None:
    api_data = computetask.orc_to_api(data)
    api_data["channel"] = channel
    if start_date is not None:
        api_data["start_date"] = parse_datetime(start_date)
    if end_date is not None:
        api_data["end_date"] = parse_datetime(end_date)
    if failure_report is not None:
        api_data["error_type"] = failure_report["error_type"]
        if "logs_address" in failure_report:
            api_data["logs_address"] = failure_report["logs_address"]
        if "owner" in failure_report:
            api_data["logs_owner"] = failure_report["owner"]
    serializer = ComputeTaskSerializer(data=api_data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Computetask already exists", asset_key=api_data["key"])


def _on_update_computetask_event(event: dict) -> None:
    """Process update computetask event to update local database."""
    logger.debug("Syncing computetask update", asset_key=event["asset_key"], event_id=event["id"])

    candidate_start_date, candidate_end_date = parse_computetask_dates_from_event(event)

    task = event["compute_task"]
    _update_computetask(task["key"], task["status"], candidate_start_date, candidate_end_date)
    compute_plan = ComputePlan.objects.get(key=task["compute_plan_key"])
    # update CP dates:
    # - after task status, to ensure proper rules are applied
    # - before CP status, to ensure dates are up-to-date when client wait on status
    compute_plan.update_dates()
    compute_plan.update_status()


def _update_computetask(
    key: str,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    failure_report: Optional[dict] = None,
) -> None:
    """Update only mutable fields: status, start_date, end_date, error_type, logs_address, logs_checksum, logs_owner"""

    compute_task = ComputeTask.objects.get(key=key)

    if status is not None:
        compute_task.status = status

    # The computetask start/end date is the timestamp of the first event related to the new status.
    # During a single event sync, we rely on the asset values to deduce if they were previous events.
    # If so, dates are not updated on the asset
    if compute_task.start_date is None and start_date is not None:
        compute_task.start_date = parse_datetime(start_date)

    if compute_task.end_date is None and end_date is not None:
        compute_task.end_date = parse_datetime(end_date)

    if failure_report is not None:
        compute_task.error_type = failure_report["error_type"]
        # logs_address only has a value if there are logs associated with the failure report, e.g. ExecutionError.
        if failure_report.get("logs_address"):
            compute_task.logs_address = failure_report["logs_address"]["storage_address"]
            compute_task.logs_checksum = failure_report["logs_address"]["checksum"]
        if "owner" in failure_report:
            compute_task.logs_owner = failure_report["owner"]

    compute_task.save()


def _on_create_computetask_output_asset_event(event: dict) -> None:
    """Process create computetask output asset event to update local database."""
    logger.debug("Syncing computetask output asset create", event_id=event["id"])
    asset = event["compute_task_output_asset"]

    _create_computetask_output_asset(
        channel=event["channel"],
        compute_task_key=asset["compute_task_key"],
        identifier=asset["compute_task_output_identifier"],
        asset_kind=asset["asset_kind"],
        asset_key=asset["asset_key"],
    )


def _create_computetask_output_asset(
    channel: str,
    compute_task_key: str,
    identifier: str,
    asset_kind: str,
    asset_key: str,
) -> None:
    task_output = ComputeTaskOutput.objects.get(
        task__key=compute_task_key,
        identifier=identifier,
        channel=channel,
    )
    ComputeTaskOutputAsset.objects.create(
        task_output=task_output,
        asset_kind=asset_kind,
        asset_key=asset_key,
        channel=channel,
    )
    for task_input in ComputeTaskInput.objects.filter(
        parent_task_key_id=compute_task_key,
        parent_task_output_identifier=identifier,
    ):
        ComputeTaskInputAsset.objects.create(
            task_input=task_input,
            asset_kind=asset_kind,
            asset_key=asset_key,
            channel=channel,
        )


def _on_create_datamanager_event(event: dict) -> None:
    """Process create datamanager event to update local database."""
    logger.debug("Syncing datamanager create", asset_key=event["asset_key"], event_id=event["id"])
    _create_datamanager(channel=event["channel"], data=event["data_manager"])


def _create_datamanager(channel: str, data: dict) -> None:
    data["channel"] = channel
    # XXX: in case of sync of MDY dumps, logs_permission won't be provided:
    #      the orchestrator and backend used to generate the dumps are both outdated.
    #      We provide a sensible default: logs are private.
    data.setdefault("logs_permission", {"public": False, "authorized_ids": [data["owner"]]})
    serializer = DataManagerSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("DataManager already exists", asset_key=data["key"])


def _on_update_datamanager_event(event: dict) -> None:
    """Process update datamanager event to update local database."""
    logger.debug("Syncing datamanager update", asset_key=event["asset_key"], event_id=event["id"])
    _update_datamanager(key=event["asset_key"], data=event["data_manager"])


def _update_datamanager(key: str, data: dict) -> None:
    """Process update datamanager event to update local database."""

    datamanager = DataManager.objects.get(key=key)
    datamanager.name = data["name"]
    datamanager.save()


def _on_create_datasample_event(event: dict) -> None:
    """Process create datasample event to update local database."""
    logger.debug("Syncing datasample create", asset_key=event["asset_key"], event_id=event["id"])
    _create_datasample(channel=event["channel"], data=event["data_sample"])


def _create_datasample(channel: str, data: dict) -> None:
    data["channel"] = channel
    serializer = DataSampleSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Datasample already exists", asset_key=data["key"])


def _on_update_datasample_event(event: dict) -> None:
    """Process update datasample event to update local database."""
    logger.debug("Syncing datasample update", asset_key=event["asset_key"], event_id=event["id"])
    _update_datasample(event["asset_key"], event["data_sample"]["data_manager_keys"])


def _update_datasample(key: str, data_manager_keys: list[str]) -> None:
    """Update only datamanager relations"""
    data_managers = DataManager.objects.filter(key__in=data_manager_keys)
    data_sample = DataSample.objects.get(key=key)
    data_sample.data_managers.set(data_managers)
    data_sample.save()


def _on_create_performance_event(event: dict) -> None:
    """Process create performance event to update local database."""
    logger.debug("Syncing performance create", asset_key=event["asset_key"], event_id=event["id"])
    _create_performance(channel=event["channel"], data=event["performance"])


def _create_performance(channel: str, data: dict) -> None:
    data["channel"] = channel
    serializer = PerformanceSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except ValidationError:
        logger.debug(
            "Performance already exists",
            compute_task_key=data["compute_task_key"],
            compute_task_output_identifier=data["compute_task_output_identifier"],
        )


def _on_create_model_event(event: dict) -> None:
    """Process create model event to update local database."""
    logger.debug("Syncing model create", asset_key=event["asset_key"], event_id=event["id"])
    _create_model(channel=event["channel"], data=event["model"])


def _create_model(channel: str, data: dict) -> None:
    data["channel"] = channel
    serializer = ModelSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Model already exists", asset_key=data["key"])


def _on_disable_model_event(event: dict) -> None:
    """Process disable model event to update local database."""
    logger.debug("Syncing model disable", asset_key=event["asset_key"], event_id=event["id"])
    _disable_model(event["asset_key"])


def _disable_model(key: str) -> None:
    """Disable model."""

    model = Model.objects.get(key=key)
    model.model_address = None
    model.save()


def _on_create_failure_report(event: dict) -> None:
    """Process create failure report event to update local database."""
    logger.debug("Syncing failure report create", asset_key=event["asset_key"], event_id=event["id"])

    asset_key = event["asset_key"]
    failure_report = event["failure_report"]
    asset_type = failure_report_pb2.FailedAssetKind.Value(failure_report["asset_type"])

    if asset_type == failure_report_pb2.FAILED_ASSET_FUNCTION:
        # Needed as this field is only in ComputeTask
        compute_task_keys = ComputeTask.objects.values_list("key", flat=True).filter(
            function_id=asset_key,
            status__in=[ComputeTask.Status.STATUS_TODO.value, ComputeTask.Status.STATUS_DOING.value],
        )

        for task_key in compute_task_keys:
            _update_computetask(key=str(task_key), failure_report={"error_type": failure_report.get("error_type")})
    else:
        _update_computetask(key=asset_key, failure_report=failure_report)


EVENT_CALLBACKS = {
    common_pb2.ASSET_COMPUTE_PLAN: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_computeplan_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_computeplan_event,
    },
    common_pb2.ASSET_FUNCTION: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_function_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_function_event,
    },
    common_pb2.ASSET_COMPUTE_TASK: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_computetask_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_computetask_event,
    },
    common_pb2.ASSET_COMPUTE_TASK_OUTPUT_ASSET: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_computetask_output_asset_event,
    },
    common_pb2.ASSET_DATA_MANAGER: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_datamanager_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_datamanager_event,
    },
    common_pb2.ASSET_DATA_SAMPLE: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_datasample_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_datasample_event,
    },
    common_pb2.ASSET_MODEL: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_model_event,
        event_pb2.EVENT_ASSET_DISABLED: _on_disable_model_event,
    },
    common_pb2.ASSET_ORGANIZATION: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_organization_event,
    },
    common_pb2.ASSET_PERFORMANCE: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_performance_event,
    },
    common_pb2.ASSET_FAILURE_REPORT: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_failure_report,
    },
}


@transaction.atomic
def sync_on_event_message(event: dict) -> None:
    """Handler to consume event.
    This function is idempotent
    """
    event_kind = event_pb2.EventKind.Value(event["event_kind"])
    asset_kind = common_pb2.AssetKind.Value(event["asset_kind"])

    callback = EVENT_CALLBACKS.get(asset_kind, {}).get(event_kind)

    if asset_kind == common_pb2.ASSET_COMPUTE_TASK:
        orc_client.add_tag_from_metadata(event["compute_task"])

    if callback:
        callback(event)
    else:
        logger.debug("Nothing to sync", event_kind=event["event_kind"], asset_kind=event["asset_kind"])
