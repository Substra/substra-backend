import structlog
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from events.dynamic_fields import fetch_failure_report_from_event
from events.dynamic_fields import parse_computetask_dates_from_event
from localrep.errors import AlreadyExistsError
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import DataManager
from localrep.models import DataSample
from localrep.models import Model
from localrep.serializers import AlgoSerializer
from localrep.serializers import ChannelNodeSerializer
from localrep.serializers import ComputePlanSerializer
from localrep.serializers import ComputeTaskSerializer
from localrep.serializers import DataManagerSerializer
from localrep.serializers import DataSampleSerializer
from localrep.serializers import ModelSerializer
from localrep.serializers import PerformanceSerializer
from orchestrator import client as orc_client
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _on_create_node_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create node event to update local database."""
    logger.debug("Syncing node create", asset_key=event["asset_key"], event_id=event["id"])

    # there is no query_node method, we extract data from the event directly
    _create_node(event["channel"], {"id": event["asset_key"], "creation_date": event["timestamp"]})


def _create_node(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = ChannelNodeSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Node already exists", node_id=data["id"], channel=data["channel"])
        return False
    else:
        return True


def _on_create_algo_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create algo event to update local database."""
    logger.debug("Syncing algo create", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_algo(event["asset_key"])
    _create_algo(event["channel"], data)


def _create_algo(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = AlgoSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Algo already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_create_computeplan_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create computeplan event to update local database."""
    logger.debug("Syncing computeplan", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_compute_plan(event["asset_key"])
    _create_computeplan(event["channel"], data)


def _create_computeplan(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = ComputePlanSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("ComputePlan already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_create_computetask_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create computetask event to update local database."""
    logger.debug("Syncing computetask create", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_task(event["asset_key"])
    _create_computetask(event["channel"], data)

    compute_plan = ComputePlan.objects.get(key=data["compute_plan_key"])
    compute_plan.update_status()


def _create_computetask(
    channel: str, data: dict, start_date: str = None, end_date: str = None, failure_report: dict = None
) -> bool:

    data["channel"] = channel
    if start_date is not None:
        data["start_date"] = parse_datetime(start_date)
    if end_date is not None:
        data["end_date"] = parse_datetime(end_date)
    if failure_report is not None:
        data["error_type"] = failure_report["error_type"]
        if "logs_address" in failure_report:
            data["logs_address"] = failure_report["logs_address"]
        if "owner" in failure_report:
            data["logs_owner"] = failure_report["owner"]
    # XXX: in case of localsync of MDY dumps, logs_permission won't be provided:
    #      the orchestrator and backend used to generate the dumps are both outdated.
    #      We provide a sensible default: logs are private.
    data.setdefault("logs_permission", {"public": False, "authorized_ids": [data["owner"]]})
    serializer = ComputeTaskSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Computetask already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_update_computetask_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process update computetask event to update local database."""
    logger.debug("Syncing computetask update", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_task(event["asset_key"])
    candidate_start_date, candidate_end_date = parse_computetask_dates_from_event(event)
    failure_report = fetch_failure_report_from_event(event, client)

    if data["status"] == ComputeTask.Status.STATUS_DONE:
        if data["category"] == ComputeTask.Category.TASK_TEST:
            _sync_performances(data["key"], client)
        else:
            _sync_models(data["key"], client)

    # Update computetask after synchronize performances and models,
    # because when the status is done, the outputs should be available.
    _update_computetask(data["key"], data["status"], candidate_start_date, candidate_end_date, failure_report)
    compute_plan = ComputePlan.objects.get(key=data["compute_plan_key"])
    # update CP dates:
    # - after task status, to ensure proper rules are applied
    # - before CP status, to ensure dates are up-to-date when client wait on status
    if data["status"] != ComputeTask.Status.STATUS_TODO:
        compute_plan.update_dates()
    compute_plan.update_status()


def _update_computetask(key: str, status: str, start_date: str, end_date: str, failure_report: dict = None) -> None:
    """Update only mutable fields: status, start_date, end_date, error_type, logs_address, logs_checksum, logs_owner"""

    compute_task = ComputeTask.objects.get(key=key)
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
        if "logs_address" in failure_report:
            compute_task.logs_address = failure_report["logs_address"]["storage_address"]
            compute_task.logs_checksum = failure_report["logs_address"]["checksum"]
        if "owner" in failure_report:
            compute_task.logs_owner = failure_report["owner"]
    compute_task.save()


def _on_create_datamanager_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create datamanager event to update local database."""
    logger.debug("Syncing datamanager create", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_datamanager(event["asset_key"])
    _create_datamanager(event["channel"], data)


def _create_datamanager(channel: str, data: dict) -> bool:
    data["channel"] = channel
    # XXX: in case of localsync of MDY dumps, logs_permission won't be provided:
    #      the orchestrator and backend used to generate the dumps are both outdated.
    #      We provide a sensible default: logs are private.
    data.setdefault("logs_permission", {"public": False, "authorized_ids": [data["owner"]]})
    serializer = DataManagerSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("DataManager already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_create_datasample_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process create datasample event to update local database."""
    logger.debug("Syncing datasample create", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_datasample(event["asset_key"])
    _create_datasample(event["channel"], data)


def _create_datasample(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = DataSampleSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Datasample already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_update_datasample_event(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Process update datasample event to update local database."""
    logger.debug("Syncing datasample update", asset_key=event["asset_key"], event_id=event["id"])

    data = client.query_datasample(event["asset_key"])
    _update_datasample(data["key"], data["data_manager_keys"])


def _update_datasample(key: str, data_manager_keys: list[str]) -> None:
    """Update only datamanager relations"""
    data_managers = DataManager.objects.filter(key__in=data_manager_keys)
    data_sample = DataSample.objects.get(key=key)
    data_sample.data_managers.set(data_managers)
    data_sample.save()


def _create_performance(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = PerformanceSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except ValidationError:
        logger.debug(
            "Performance already exists", compute_task_key=data["compute_task_key"], metric_key=data["metric_key"]
        )
        return False
    else:
        return True


def _create_model(channel: str, data: dict) -> bool:
    data["channel"] = channel
    serializer = ModelSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Model already exists", asset_key=data["key"])
        return False
    else:
        return True


def _on_disable_model_event(event: dict, _client: orc_client.OrchestratorClient) -> None:
    """Process disable model event to update local database."""
    logger.debug("Syncing model disable", asset_key=event["asset_key"], event_id=event["id"])

    _disable_model(event["asset_key"])


def _disable_model(key: str) -> None:
    """Disable model."""

    model = Model.objects.get(key=key)
    model.model_address = None
    model.save()


EVENT_CALLBACKS = {
    common_pb2.ASSET_COMPUTE_PLAN: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_computeplan_event,
    },
    common_pb2.ASSET_ALGO: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_algo_event,
    },
    common_pb2.ASSET_COMPUTE_TASK: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_computetask_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_computetask_event,
    },
    common_pb2.ASSET_DATA_MANAGER: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_datamanager_event,
    },
    common_pb2.ASSET_DATA_SAMPLE: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_datasample_event,
        event_pb2.EVENT_ASSET_UPDATED: _on_update_datasample_event,
    },
    common_pb2.ASSET_MODEL: {
        event_pb2.EVENT_ASSET_DISABLED: _on_disable_model_event,
    },
    common_pb2.ASSET_NODE: {
        event_pb2.EVENT_ASSET_CREATED: _on_create_node_event,
    },
}


@transaction.atomic
def sync_on_event_message(event: dict, client: orc_client.OrchestratorClient) -> None:
    """Handler to consume event.
    This function is idempotent (can be called in sync and resync mode)
    """
    event_kind = event_pb2.EventKind.Value(event["event_kind"])
    asset_kind = common_pb2.AssetKind.Value(event["asset_kind"])

    callback = EVENT_CALLBACKS.get(asset_kind, {}).get(event_kind)

    if callback:
        callback(event, client)
    else:
        logger.debug("Nothing to sync", event_kind=event["event_kind"], asset_kind=event["asset_kind"])


def resync_algos(client: orc_client.OrchestratorClient):
    logger.info("Resyncing algos")
    algos = client.query_algos(
        categories=[
            algo_pb2.AlgoCategory.ALGO_SIMPLE,
            algo_pb2.AlgoCategory.ALGO_COMPOSITE,
            algo_pb2.AlgoCategory.ALGO_AGGREGATE,
        ]
    )  # TODO: Add filter on last_modification_date
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in algos:
        is_created = _create_algo(client.channel_name, data)
        if is_created:
            logger.debug("Created new algo", asset_key=data["key"])
            nb_new_assets += 1
        else:
            logger.debug("Skipped algo", asset_key=data["key"])
            nb_skipped_assets += 1

    logger.info("Done resync algos", nb_new_assets=nb_new_assets, nb_skipped_assets=nb_skipped_assets)


def resync_datamanagers(client: orc_client.OrchestratorClient):
    logger.info("Resyncing datamanagers")
    datamanagers = client.query_datamanagers()  # TODO: Add filter on last_modification_date
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in datamanagers:
        is_created = _create_datamanager(client.channel_name, data)
        if is_created:
            logger.debug("Created new datamanager", asset_key=data["key"])
            nb_new_assets += 1
        else:
            logger.debug("Skipped datamanager", asset_key=data["key"])
            nb_skipped_assets += 1

    logger.info("Done resync datamanagers", nb_new_assets=nb_new_assets, nb_skipped_assets=nb_skipped_assets)


def resync_datasamples(client: orc_client.OrchestratorClient):
    logger.info("Resyncing datasamples")
    datasamples = client.query_datasamples()  # TODO: Add filter on last_modification_date
    nb_new_assets = 0
    nb_updated_assets = 0

    for data in datasamples:
        is_created = _create_datasample(client.channel_name, data)
        if is_created:
            logger.debug("Created new datasample", asset_key=data["key"])
            nb_new_assets += 1
        else:
            _update_datasample(data["key"], data["data_manager_keys"])
            logger.debug("Updated datasample", asset_key=data["key"])
            nb_updated_assets += 1

    logger.info("Done resync datasamples", nb_new_assets=nb_new_assets, nb_updated_assets=nb_updated_assets)


def resync_computeplans(client: orc_client.OrchestratorClient):
    logger.info("Resyncing computeplans")

    computeplans = client.query_compute_plans()  # TODO: Add filter on last_modification_date
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in computeplans:
        is_created = _create_computeplan(client.channel_name, data)
        if data["status"] != ComputePlan.Status.PLAN_STATUS_TODO:
            compute_plan = ComputePlan.objects.get(key=data["key"])
            compute_plan.update_dates()
        if is_created:
            logger.debug("Created new computeplan", asset_key=data["key"])
            nb_new_assets += 1
        else:
            logger.debug("Skipped computeplan", asset_key=data["key"])
            nb_skipped_assets += 1
    logger.info("Done resync computeplans", nb_new_assets=nb_new_assets, nb_skipped_assets=nb_skipped_assets)


def _sync_performances(compute_task_key: str, client: orc_client.OrchestratorClient) -> None:
    logger.info("Syncing performances ", task_key=compute_task_key)
    performances = client.get_compute_task_performances(compute_task_key)
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in performances:
        is_created = _create_performance(client.channel_name, data)
        if is_created:
            logger.debug(
                "Created new performance", compute_task_key=data["compute_task_key"], metric_key=data["metric_key"]
            )
            nb_new_assets += 1
        else:
            logger.debug(
                "Skipped performance", compute_task_key=data["compute_task_key"], metric_key=data["metric_key"]
            )
            nb_skipped_assets += 1

    logger.info(
        "Done creating performances for task",
        task_key=compute_task_key,
        nb_new_assets=nb_new_assets,
        nb_skipped_assets=nb_skipped_assets,
    )


def _sync_models(compute_task_key: str, client: orc_client.OrchestratorClient) -> None:
    logger.info("Syncing models ", task_key=compute_task_key)
    models = client.get_computetask_output_models(compute_task_key)
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in models:
        is_created = _create_model(client.channel_name, data)
        if is_created:
            logger.debug("Created new model", asset_key=data["key"])
            nb_new_assets += 1
        else:
            logger.debug("Skipped model", asset_key=data["key"])
            nb_skipped_assets += 1


def resync_computetasks(client: orc_client.OrchestratorClient):
    logger.info("Resyncing computetasks")
    computetasks = client.query_tasks()  # TODO: Add filter on last_modification_date
    nb_new_assets = 0
    nb_updated_assets = 0

    for data in computetasks:
        start_date, end_date, failure_report = None, None, None
        events = client.query_events(
            asset_key=data["key"],
            asset_kind=common_pb2.ASSET_COMPUTE_TASK,
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
        )
        for event in events:
            candidate_start_date, candidate_end_date = parse_computetask_dates_from_event(event)
            # The computetask start/end date is the timestamp of the first event related to the new status
            if start_date is None and candidate_start_date is not None:
                start_date = candidate_start_date
            if end_date is None and candidate_end_date is not None:
                end_date = candidate_end_date
            if failure_report is None:
                failure_report = fetch_failure_report_from_event(event, client)

        is_created = _create_computetask(client.channel_name, data, start_date, end_date, failure_report)
        if is_created:
            logger.debug("Created new computetask", asset_key=data["key"])
            nb_new_assets += 1
        else:
            _update_computetask(data["key"], data["status"], start_date, end_date, failure_report)
            logger.debug("Updated computetask", asset_key=data["key"])
            nb_updated_assets += 1

        if data["status"] == ComputeTask.Status.STATUS_DONE:
            if data["category"] == ComputeTask.Category.TASK_TEST:
                _sync_performances(data["key"], client)
            else:
                _sync_models(data["key"], client)

    for compute_plan in ComputePlan.objects.all():
        compute_plan.update_status()

    logger.info("Done resync computetasks", nb_new_assets=nb_new_assets, nb_updated_assets=nb_updated_assets)


def resync_nodes(client: orc_client.OrchestratorClient):
    logger.info("Resyncing nodes")
    nodes = client.query_nodes()
    nb_new_assets = 0
    nb_skipped_assets = 0

    for data in nodes:
        is_created = _create_node(client.channel_name, data)
        if is_created:
            logger.debug("Created new node", node_id=data["id"])
            nb_new_assets += 1
        else:
            logger.debug("Skipped node", node_id=data["id"])
            nb_skipped_assets += 1

    logger.info("Done resync nodes", nb_new_assets=nb_new_assets, nb_skipped_assets=nb_skipped_assets)


def resync() -> None:
    """Resync the local asset representation.
    Fetch all assets from the orchestrator that are not present locally in the backend.
    """
    logger.info("Resyncing local representation")

    for channel_name in settings.LEDGER_CHANNELS.keys():
        logger.info("Resyncing for channel", channel=channel_name)
        with get_orchestrator_client(channel_name) as client:
            resync_nodes(client)
            resync_algos(client)
            resync_datamanagers(client)
            resync_datasamples(client)
            resync_computeplans(client)
            resync_computetasks(client)
