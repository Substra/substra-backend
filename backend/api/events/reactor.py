import threading

import structlog
from django.conf import settings
from django.db import close_old_connections

import orchestrator
from api.events import health
from api.events import sync
from api.models import LastEvent
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger("events")


def on_event(payload):
    try:
        logger.debug("Received payload", payload=payload)
        sync.sync_on_event_message(payload)
    except Exception as e:
        logger.exception("Error processing message", e=e)
        raise
    finally:
        # we are not sure that, in a django context, all db connection are closed automatically
        # when the function ends
        close_old_connections()


def consume_channel(client: orchestrator.Client, channel_name: str, exception_raised: threading.Event):
    try:

        structlog.contextvars.bind_contextvars(channel_name=channel_name)
        logger.info("Attempting to connect to orchestrator gRPC stream")

        last_event, _ = LastEvent.objects.get_or_create(channel=channel_name)

        logger.info("Starting to consume messages from orchestrator gRPC stream", start_event_id=last_event.event_id)
        for event in client.subscribe_to_events(channel_name=channel_name, start_event_id=last_event.event_id):
            on_event(event)
            last_event.event_id = event["id"]
            last_event.save()

    except Exception as e:
        if not exception_raised.is_set():
            logger.exception("Error during events consumption", e=e)
            exception_raised.set()
            raise


def consume(health_service: health.HealthService):
    client = get_orchestrator_client()
    exception_raised = threading.Event()

    consumers = [
        threading.Thread(
            target=consume_channel,
            args=(
                client,
                channel_name,
                exception_raised,
            ),
        )
        for channel_name in settings.LEDGER_CHANNELS.keys()
    ]

    for consumer in consumers:
        consumer.start()

    health_service.ready()

    exception_raised.wait()
    client.grpc_channel.close()

    for consumer in consumers:
        consumer.join()

    raise RuntimeError("Orchestrator gRPC streams consumption interrupted")
