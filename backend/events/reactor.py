import threading

import structlog
from django.conf import settings
from django.db import close_old_connections
from google.protobuf import json_format

import orchestrator
import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
from events import health
from events import localsync
from localrep.models import LastEvent
from substrapp.orchestrator import get_orchestrator_client
from substrapp.tasks.tasks_compute_plan import queue_delete_cp_pod_and_dirs_and_optionally_images
from substrapp.tasks.tasks_compute_task import queue_compute_task
from substrapp.tasks.tasks_remove_intermediary_models import queue_remove_intermediary_models_from_db
from substrapp.tasks.tasks_remove_intermediary_models import remove_intermediary_models_from_buffer
from substrapp.utils import get_owner

logger = structlog.get_logger("events")


def on_computetask_event(payload):
    my_organisation = get_owner()
    asset_key = payload["asset_key"]
    channel_name = payload["channel"]
    event_kind = payload["event_kind"]
    task = payload["compute_task"]
    targeted_organisation = task["worker"]

    logger.info("Processing task", asset_key=asset_key, kind=event_kind, status=task["status"])

    event_task_status = computetask_pb2.ComputeTaskStatus.Value(task["status"])

    if event_task_status in [
        computetask_pb2.STATUS_DONE,
        computetask_pb2.STATUS_CANCELED,
        computetask_pb2.STATUS_FAILED,
    ]:
        with get_orchestrator_client(channel_name) as client:
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
            asset_key=asset_key,
            kind=event_kind,
            status=task["status"],
        )
        return

    grpc_task = computetask_pb2.ComputeTask()
    json_format.ParseDict(task, grpc_task, ignore_unknown_fields=True)
    orc_task = orchestrator.ComputeTask.from_grpc(grpc_task)
    queue_compute_task(channel_name, task=orc_task)


def on_model_event(payload):
    asset_key = payload["asset_key"]
    event_kind = payload["event_kind"]

    logger.info("Processing model", asset_key=asset_key, kind=event_kind)

    if event_pb2.EventKind.Value(event_kind) == event_pb2.EVENT_ASSET_DISABLED:

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


def on_event(payload):
    try:
        logger.debug("Received payload", payload=payload)
        localsync.sync_on_event_message(payload)
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
