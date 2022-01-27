import structlog
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from localrep.errors import AlreadyExistsError
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _save_event(event: dict):
    """Save processed event."""
    from localrep.serializers import EventSerializer

    logger.debug("Syncing event", data=event)

    serializer = EventSerializer(data=event)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Event already exists", asset_key=event["asset_key"], event_id=event["id"])


def _on_create_algo_event(event: dict):
    """Process create algo event to update local database."""
    from localrep.serializers import AlgoSerializer

    logger.debug("Syncing algo create", asset_key=event["asset_key"], event_id=event["id"])

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_algo(event["asset_key"])
    data["channel"] = event["channel"]
    serializer = AlgoSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Algo already exists", asset_key=event["asset_key"], event_id=event["id"])


def _on_create_datamanager_event(event: dict):
    """Process create datamanager event to update local database."""
    from localrep.serializers import DataManagerSerializer

    logger.debug("Syncing datamanager create", asset_key=event["asset_key"], event_id=event["id"])

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_datamanager(event["asset_key"])
    data["channel"] = event["channel"]
    # XXX: in case of localsync of MDY dumps, logs_permission won't be provided:
    #      the orchestrator and backend used to generate the dumps are both outdated.
    #      We provide a sensible default: logs are private.
    data["logs_permission"] = event.get("logs_permission", {"public": False, "authorized_ids": [data["owner"]]})
    serializer = DataManagerSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Datamanager already exists", asset_key=event["asset_key"], event_id=event["id"])


def _on_create_datasample_event(event: dict):
    """Process create datasample event to update local database."""
    from localrep.serializers import DataSampleSerializer

    logger.debug("Syncing datasample create", asset_key=event["asset_key"], event_id=event["id"])

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_datasample(event["asset_key"])
    data["channel"] = event["channel"]
    serializer = DataSampleSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Datasample already exists", asset_key=event["asset_key"], event_id=event["id"])


def _on_update_datasample_event(event: dict):
    """Process update datasample event to update local database."""
    from localrep.models import DataManager
    from localrep.models import DataSample

    logger.debug("Syncing datasample update", asset_key=event["asset_key"], event_id=event["id"])

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_datasample(event["asset_key"])
    data["channel"] = event["channel"]
    data_managers = DataManager.objects.filter(key__in=data["data_manager_keys"])
    data_sample = DataSample.objects.get(key=data["key"])
    data_sample.data_managers.set(data_managers)
    data_sample.save()


def _on_create_metric_event(event: dict):
    """Process create metric event to update local database."""
    from localrep.serializers import MetricSerializer

    logger.debug("Syncing metric create", asset_key=event["asset_key"], event_id=event["id"])

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_metric(event["asset_key"])
    data["channel"] = event["channel"]
    serializer = MetricSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Metric already exists", asset_key=event["asset_key"], event_id=event["id"])


@transaction.atomic
def sync_on_event_message(event: dict):
    """Handler to consume event.
    This function is idempotent (can be called in sync and resync mode)
    """
    event_kind = event_pb2.EventKind.Value(event["event_kind"])
    asset_kind = common_pb2.AssetKind.Value(event["asset_kind"])

    if (event_kind, asset_kind) == (event_pb2.EVENT_ASSET_CREATED, common_pb2.ASSET_ALGO):
        _on_create_algo_event(event)
    elif (event_kind, asset_kind) == (event_pb2.EVENT_ASSET_CREATED, common_pb2.ASSET_DATA_MANAGER):
        _on_create_datamanager_event(event)
    elif (event_kind, asset_kind) == (event_pb2.EVENT_ASSET_CREATED, common_pb2.ASSET_DATA_SAMPLE):
        _on_create_datasample_event(event)
    elif (event_kind, asset_kind) == (event_pb2.EVENT_ASSET_UPDATED, common_pb2.ASSET_DATA_SAMPLE):
        _on_update_datasample_event(event)
    elif (event_kind, asset_kind) == (event_pb2.EVENT_ASSET_CREATED, common_pb2.ASSET_METRIC):
        _on_create_metric_event(event)
    else:
        logger.debug("Nothing to sync", event_kind=event["event_kind"], asset_kind=event["asset_kind"])

    _save_event(event)


def resync():
    """Resync the local asset representation.
    Fetch all events from the orchestrator that are not present locally in the backend
    and process them to sync the local representation.
    """
    logger.info("Resyncing local representation")

    # get latest event processed locally
    from localrep.models import Event

    try:
        local_latest_event = Event.objects.latest("timestamp").timestamp
    except ObjectDoesNotExist:
        local_latest_event = None

    logger.info("Syncing orchestrator events since the latest local event", timestamp=local_latest_event)

    for channel_name in settings.LEDGER_CHANNELS.keys():
        with get_orchestrator_client(channel_name) as client:
            event_count = 0
            # Fetch events assets created
            for event_count, event in enumerate(
                client.query_events_generator(
                    start=local_latest_event.isoformat() if local_latest_event is not None else None,
                ),
                start=1,
            ):
                sync_on_event_message(event)

            logger.info(
                f"{event_count} orchestrator events synced since the latest local event",
                timestamp=local_latest_event,
                channel=channel_name,
            )
