import json
import ssl
import time
from contextlib import closing

import pika
import structlog
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


def on_message(channel, method_frame, header_frame, body):
    try:
        payload = json.loads(body.decode())
        logger.debug("Received payload", payload=payload)
        with get_orchestrator_client(payload["channel"]) as client:
            localsync.sync_on_event_message(payload, client)
        on_message_compute_engine(payload)
    except Exception as e:
        logger.exception("Error processing message", e=e)
        # we choose to requeue the message on error
        channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=True)
        raise
    else:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    finally:
        # we are not sure that, in a django context, all db connection are closed automatically
        # when the function ends
        close_old_connections()


def get_rabbitmq_connection():
    credentials = pika.credentials.PlainCredentials(
        username=settings.ORCHESTRATOR_RABBITMQ_AUTH_USER, password=settings.ORCHESTRATOR_RABBITMQ_AUTH_PASSWORD
    )

    ssl_options = None
    if settings.ORCHESTRATOR_RABBITMQ_TLS_ENABLED:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_verify_locations(settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CACERT_PATH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(
            settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CERT_PATH,
            settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_KEY_PATH,
        )
        ssl_options = pika.SSLOptions(context, settings.ORCHESTRATOR_RABBITMQ_HOST)

    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.ORCHESTRATOR_RABBITMQ_HOST,
            port=settings.ORCHESTRATOR_RABBITMQ_PORT,
            credentials=credentials,
            ssl_options=ssl_options,
            blocked_connection_timeout=ORCHESTRATOR_RABBITMQ_CONNECTION_TIMEOUT,
            heartbeat=60,
        )
    )


def consume():

    # Queues are defined by the orchestrator and are named according user login
    queue_name = settings.ORCHESTRATOR_RABBITMQ_AUTH_USER

    log = logger.bind(queue=queue_name)

    log.info("Attempting to connect to orchestrator RabbitMQ")

    # It's not necessary to disconnect the channel as connection close will do it for us
    # close will be called by the closing contextlib function
    # https://pika.readthedocs.io/en/stable/modules/connection.html#pika.connection.Connection.close
    with closing(get_rabbitmq_connection()) as connection:
        log.info("Connected to orchestrator RabbitMQ")
        channel = connection.channel()  # Creating channel
        channel.queue_declare(queue=queue_name, passive=True)  # Declaring queue
        channel.basic_consume(queue=queue_name, on_message_callback=on_message, auto_ack=False)
        log.info("Starting to consume messages from orchestrator RabbitMQ")
        channel.start_consuming()


def resync():
    while True:  # watchmedo intercepts exit signals and blocks k8s pods restart
        try:
            localsync.resync()
        except Exception as e:
            time.sleep(30)
            logger.exception("Retry connecting to orchestrator GRPC api", e=e)
        else:
            break
