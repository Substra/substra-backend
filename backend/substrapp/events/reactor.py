import threading

import structlog
from django.conf import settings
from django.db import close_old_connections
from google.protobuf import json_format

import orchestrator
import orchestrator.common_pb2 as common_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
from builder.tasks.tasks_build_image import build_image
from orchestrator import function_pb2
from orchestrator import model_pb2
from substrapp.events import handler_compute_engine
from substrapp.events import health
from substrapp.models import WorkerLastEvent
from substrapp.orchestrator import get_orchestrator_client
from substrapp.task_routing import WORKER_QUEUE
from substrapp.task_routing import get_builder_queue
from substrapp.tasks.tasks_compute_plan import queue_delete_cp_pod_and_dirs_and_optionally_images
from substrapp.tasks.tasks_compute_task import queue_compute_task
from substrapp.tasks.tasks_save_image import save_image_task

logger = structlog.get_logger("events")
_MY_ORGANIZATION: str = settings.LEDGER_MSP_ID


def on_computetask_event(payload):
    asset_key = payload["asset_key"]
    channel_name = payload["channel"]
    event_kind = payload["event_kind"]
    task = payload["compute_task"]
    grpc_task = computetask_pb2.ComputeTask()
    json_format.ParseDict(task, grpc_task, ignore_unknown_fields=True)
    orc_task = orchestrator.ComputeTask.from_grpc(grpc_task)

    logger.info("Processing task", asset_key=asset_key, kind=event_kind, status=orc_task.status)

    if orc_task.status in [
        orchestrator.ComputeTaskStatus.STATUS_DONE,
        orchestrator.ComputeTaskStatus.STATUS_CANCELED,
        orchestrator.ComputeTaskStatus.STATUS_FAILED,
    ]:
        with get_orchestrator_client(channel_name) as client:
            handler_compute_engine.handle_finished_tasks(client, channel_name, orc_task)

            if not client.is_compute_plan_running(orc_task.compute_plan_key):
                logger.info(
                    "Compute plan finished",
                    plan=orc_task.compute_plan_key,
                    asset_key=asset_key,
                    kind=event_kind,
                )

                queue_delete_cp_pod_and_dirs_and_optionally_images(
                    channel_name, compute_plan_key=orc_task.compute_plan_key
                )

    if orc_task.status != orchestrator.ComputeTaskStatus.STATUS_TODO:
        return

    if event_pb2.EventKind.Value(event_kind) not in [event_pb2.EVENT_ASSET_CREATED, event_pb2.EVENT_ASSET_UPDATED]:
        return

    if orc_task.worker != _MY_ORGANIZATION:
        logger.info(
            "Skipping task: this organisation is not the targeted organisation",
            my_organisation=_MY_ORGANIZATION,
            targeted_organisation=orc_task.worker,
            asset_key=asset_key,
            kind=event_kind,
            status=orc_task.status,
        )
        return

    queue_compute_task(channel_name, task=orc_task)


def on_function_event(payload):
    asset_key = payload["asset_key"]
    channel_name = payload["channel"]
    event_kind = payload["event_kind"]
    function = payload["function"]
    grpc_function = function_pb2.Function()
    json_format.ParseDict(function, grpc_function)
    orc_function = orchestrator.Function.from_grpc(grpc_function)
    logger.info("Processing function", asset_key=asset_key, kind=event_kind)

    if event_pb2.EventKind.Value(event_kind) == event_pb2.EVENT_ASSET_CREATED:
        if orc_function.owner == _MY_ORGANIZATION:
            function_key = orc_function.key
            builder_queue = get_builder_queue()
            logger.info(
                "Assigned function to builder queue",
                asset_key=function_key,
                queue=builder_queue,
            )

            building_params = {
                "channel_name": channel_name,
                "function_serialized": orc_function.json(),
            }
            (
                # TODO switch to function.model_dump_json() as soon as pydantic is updated to > 2.0
                build_image.si(**building_params).set(queue=builder_queue, task_id=function_key)
                | save_image_task.si(**building_params).set(queue=WORKER_QUEUE, task_id=function_key)
            ).apply_async()

        else:
            logger.debug("Function not belonging to this organization, skipping building", asset_key=orc_function.key)


def on_model_event(payload):
    event_kind = payload["event_kind"]
    channel_name = payload["channel"]
    model = payload["model"]
    grpc_model = model_pb2.Model()
    json_format.ParseDict(model, grpc_model, ignore_unknown_fields=True)
    orc_model = orchestrator.Model.from_grpc(grpc_model)

    logger.info("Processing model", asset_key=orc_model.key, kind=event_kind)

    if event_pb2.EventKind.Value(event_kind) == event_pb2.EVENT_ASSET_DISABLED:
        handler_compute_engine.handle_disabled_model(channel_name, orc_model)


def on_message_compute_engine(payload):
    """Compute engine handler to consume event."""
    asset_kind = common_pb2.AssetKind.Value(payload["asset_kind"])
    if asset_kind == common_pb2.ASSET_COMPUTE_TASK:
        on_computetask_event(payload)
    elif asset_kind == common_pb2.ASSET_MODEL:
        on_model_event(payload)
    elif asset_kind == common_pb2.ASSET_FUNCTION:
        logger.info("Processing function", asset_kind=payload["asset_kind"])
        on_function_event(payload)
    else:
        logger.debug("Nothing to do", asset_kind=payload["asset_kind"])


def on_event(payload):
    try:
        logger.debug("Received payload", payload=payload)
        on_message_compute_engine(payload)
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

        last_event, _ = WorkerLastEvent.objects.get_or_create(channel=channel_name)

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
