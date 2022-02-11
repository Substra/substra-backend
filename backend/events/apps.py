import asyncio
import contextlib
import functools
import json
import ssl
import time

import aio_pika
import structlog
from django.apps import AppConfig
from django.conf import settings
from django.db import close_old_connections

import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
from events import localsync
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner

ORCHESTRATOR_RABBITMQ_CONNECTION_TIMEOUT = 30

logger = structlog.get_logger("events")


@contextlib.contextmanager
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


def on_computetask_event(payload):
    my_organisation = get_owner()
    asset_key = payload["asset_key"]
    channel_name = payload["channel"]
    event_kind = payload["event_kind"]
    metadata = payload["metadata"]
    targeted_organisation = metadata["worker"]

    logger.info("Processing task", asset_key=asset_key, kind=event_kind, status=metadata["status"])

    event_task_status = computetask_pb2.ComputeTaskStatus.Value(metadata["status"])

    if event_task_status in [
        computetask_pb2.STATUS_DONE,
        computetask_pb2.STATUS_CANCELED,
        computetask_pb2.STATUS_FAILED,
    ]:
        with get_orchestrator_client(channel_name) as client:
            task = client.query_task(asset_key)

            # Handle intermediary models
            models = []
            for parent_key in task["parent_task_keys"]:
                models.extend(client.get_computetask_output_models(parent_key))

            model_keys = [
                model["key"]
                for model in models
                if model["owner"] == my_organisation and client.can_disable_model(model["key"])
            ]
            if model_keys:
                from substrapp.tasks.tasks_remove_intermediary_models import queue_remove_intermediary_models_from_db

                queue_remove_intermediary_models_from_db(channel_name, model_keys)

            # Handle compute plan if necessary
            compute_plan = client.query_compute_plan(task["compute_plan_key"])

            if computeplan_pb2.ComputePlanStatus.Value(compute_plan["status"]) in [
                computeplan_pb2.PLAN_STATUS_DONE,
                computeplan_pb2.PLAN_STATUS_CANCELED,
                computeplan_pb2.PLAN_STATUS_FAILED,
            ]:
                logger.info(
                    "Compute plan finished",
                    plan=compute_plan["key"],
                    status=compute_plan["status"],
                    asset_key=asset_key,
                    kind=event_kind,
                )
                from substrapp.tasks.tasks_compute_plan import queue_delete_cp_pod_and_dirs_and_optionally_images

                queue_delete_cp_pod_and_dirs_and_optionally_images(channel_name, compute_plan=compute_plan)

    if event_task_status != computetask_pb2.STATUS_TODO:
        return

    if event_pb2.EventKind.Value(event_kind) not in [event_pb2.EVENT_ASSET_CREATED, event_pb2.EVENT_ASSET_UPDATED]:
        return

    if targeted_organisation != my_organisation:
        logger.info(
            "Skipping task: this organisation is not the targeted organisation",
            my_organisation=my_organisation,
            targeted_organisation=targeted_organisation,
            assert_key=asset_key,
            kind=event_kind,
            status=metadata["status"],
        )
        return

    with get_orchestrator_client(channel_name) as client:
        task = client.query_task(asset_key)

    from substrapp.tasks.tasks_prepare_task import queue_prepare_task

    queue_prepare_task(channel_name, task=task)


def on_model_event(payload):
    asset_key = payload["asset_key"]
    event_kind = payload["event_kind"]

    logger.info("Processing model", asset_key=asset_key, kind=event_kind)

    if event_pb2.EventKind.Value(event_kind) == event_pb2.EVENT_ASSET_DISABLED:
        from substrapp.tasks.tasks_remove_intermediary_models import remove_intermediary_models_from_buffer

        # This task is broadcasted to all worker (see the broadcast defined in backend/celery.py)
        remove_intermediary_models_from_buffer.apply_async([asset_key])


def on_message_compute_engine(payload):
    """Compute engine handler to consume event."""
    asset_kind = common_pb2.AssetKind.Value(payload["asset_kind"])
    if asset_kind == common_pb2.ASSET_COMPUTE_TASK:
        on_computetask_event(payload)
    elif asset_kind == common_pb2.ASSET_MODEL:
        on_model_event(payload)
    else:
        logger.debug("Nothing to do", asset_kind=payload["asset_kind"])


async def on_message(event: asyncio.Event, message: aio_pika.IncomingMessage):
    async with message.process(requeue=True):
        try:
            payload = json.loads(message.body)
            logger.debug("Received payload", payload=payload)
            event.set()  # for watch_message_activity
            with get_orchestrator_client(payload["channel"]) as client:
                localsync.sync_on_event_message(payload, client)
            on_message_compute_engine(payload)
        except Exception as e:
            logger.exception("Error processing message", e=e)
            raise
        finally:
            # Django does not automatically close the DB connection when the async process ends
            close_old_connections()


async def watch_message_activity(event: asyncio.Event):
    timeout = settings.ORCHESTRATOR_RABBITMQ_ACTIVTY_TIMEOUT
    while True:
        try:
            # wait for event to be set by on_message
            await asyncio.wait_for(event.wait(), timeout)
        except asyncio.TimeoutError:
            logger.warning("No message received from orchestrator RabbitMQ queue after timeout", timeout=timeout)
            # Not receiving event means we have a connection issue or the platform is in standby.
            # Either way, we raise to trigger a reconnection.
            raise

        else:
            event.clear()


async def consume(loop, event: asyncio.Event):
    # Queues are defined by the orchestrator
    queue_name = settings.ORCHESTRATOR_RABBITMQ_AUTH_USER

    log = logger.bind(
        queue=queue_name,
    )

    ssl_options = None
    if settings.ORCHESTRATOR_RABBITMQ_TLS_ENABLED:
        ssl_options = {
            "ca_certs": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CACERT_PATH,
            "certfile": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CERT_PATH,
            "keyfile": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_KEY_PATH,
            "cert_reqs": ssl.CERT_REQUIRED,
        }

    log.info("Attempting to connect to orchestrator RabbitMQ")

    connection = await aio_pika.connect_robust(
        host=settings.ORCHESTRATOR_RABBITMQ_HOST,
        port=settings.ORCHESTRATOR_RABBITMQ_PORT,
        login=settings.ORCHESTRATOR_RABBITMQ_AUTH_USER,
        password=settings.ORCHESTRATOR_RABBITMQ_AUTH_PASSWORD,
        ssl=settings.ORCHESTRATOR_RABBITMQ_TLS_ENABLED,
        ssl_options=ssl_options,
        loop=loop,
        timeout=ORCHESTRATOR_RABBITMQ_CONNECTION_TIMEOUT,
    )

    log.info("Connected to orchestrator RabbitMQ")

    # Creating channel
    channel = await connection.channel()  # type: aio_pika.Channel

    # Declaring queue
    queue = await channel.get_queue(queue_name, ensure=True)  # type: aio_pika.Queue

    on_message_timeout = functools.partial(on_message, event)
    await queue.consume(on_message_timeout)

    return connection


def consume_messages():
    with get_event_loop() as loop:
        on_received_message_event = asyncio.Event()
        # Run: consume orchestrator new events
        while True:  # watchmedo intercepts exit signals and blocks k8s pods restart
            try:
                connection = loop.run_until_complete(consume(loop, on_received_message_event))
            except Exception as e:
                time.sleep(5)
                logger.error("Retry connecting to orchestrator RabbitMQ queue", error=e)
            else:
                break
        try:
            loop.run_until_complete(watch_message_activity(on_received_message_event))
        finally:
            loop.run_until_complete(connection.close())


class EventsConfig(AppConfig):
    name = "events"
    logger.info("starting event app")

    def ready(self):
        # Init: resync all orchestrator assets
        while True:  # watchmedo intercepts exit signals and blocks k8s pods restart
            try:
                localsync.resync()
            except Exception as e:
                time.sleep(30)
                logger.error("Retry connecting to orchestrator GRPC api", error=e)
            else:
                break
        while True:
            try:
                consume_messages()
            except asyncio.TimeoutError as e:
                logger.error("Restart event app", error=e)
