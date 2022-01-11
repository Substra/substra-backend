import structlog
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.dateparse import parse_datetime

import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _save_event(event: dict):
    """Save processed event."""
    from localrep.errors import AlreadyExistsError
    from localrep.serializers import EventSerializer

    logger.debug("Syncing event", data=event)

    serializer = EventSerializer(data=event)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Event already exists", asset_key=event["asset_key"], event_id=event["id"])


def _algo_event(event: dict):
    """Process algo event to update local database."""
    logger.debug("Syncing algo", asset_key=event["asset_key"], event_id=event["id"])

    from localrep.errors import AlreadyExistsError
    from localrep.serializers import AlgoSerializer
    from substrapp.orchestrator import get_orchestrator_client

    with get_orchestrator_client(event["channel"]) as client:
        data = client.query_algo(event["asset_key"])
    data["channel"] = event["channel"]
    serializer = AlgoSerializer(data=data)
    try:
        serializer.save_if_not_exists()
    except AlreadyExistsError:
        logger.debug("Algo already exists", asset_key=event["asset_key"], event_id=event["id"])


@transaction.atomic
def sync_on_event_message(event: dict):
    """Handler to consume event.
    This function is idempotent (can be called in sync and resync mode)
    """
    asset_kind = common_pb2.AssetKind.Value(event["asset_kind"])

    if asset_kind == common_pb2.ASSET_ALGO:
        _algo_event(event)
    else:
        logger.debug("Nothing to sync", asset_kind=event["asset_kind"])

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
            # Fetch events assets created
            for event in client.query_events_generator(event_kind=event_pb2.EVENT_ASSET_CREATED):
                if not local_latest_event or parse_datetime(event["timestamp"]) >= local_latest_event:
                    sync_on_event_message(event)
