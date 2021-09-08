import asyncio
import json
import logging
import contextlib
import time
import ssl
from django.apps import AppConfig

from django.conf import settings

import aio_pika

import substrapp.orchestrator.computetask_pb2 as computetask_pb2
import substrapp.orchestrator.computeplan_pb2 as computeplan_pb2
import substrapp.orchestrator.common_pb2 as common_pb2
import substrapp.orchestrator.event_pb2 as event_pb2
from substrapp.orchestrator.api import get_orchestrator_client

from substrapp.tasks.tasks_prepare_task import prepare_task
from substrapp.utils import get_owner

from celery.result import AsyncResult

from substrapp.tasks.tasks_compute_plan import on_compute_plan_finished
from substrapp.tasks.tasks_remove_intermediary_models import (
    remove_intermediary_models,
    remove_intermediary_models_from_buffer
)


logger = logging.getLogger('events')


@contextlib.contextmanager
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


def on_computetask_event(payload):
    current_worker = get_owner()
    worker_queue = f"{settings.ORG_NAME}.worker"
    asset_key = payload['asset_key']
    channel_name = payload['channel']
    event_kind = payload['event_kind']
    metadata = payload['metadata']

    logger.info(f'Processing task {asset_key}: type={event_kind} event status={metadata["status"]}')

    event_task_status = computetask_pb2.ComputeTaskStatus.Value(metadata["status"])

    if event_task_status in [
            computetask_pb2.STATUS_DONE,
            computetask_pb2.STATUS_CANCELED,
            computetask_pb2.STATUS_FAILED]:
        with get_orchestrator_client(channel_name) as client:
            task = client.query_task(asset_key)

            # Handle intermediary models
            models = []
            for parent_key in task['parent_task_keys']:
                models.extend(client.get_computetask_output_models(parent_key))

            model_keys = [model['key'] for model in models
                          if model['owner'] == current_worker and client.can_disable_model(model['key'])]
            if model_keys:
                remove_intermediary_models.apply_async((channel_name, model_keys), queue=worker_queue)

            compute_plan = client.query_compute_plan(task['compute_plan_key'])
            if computeplan_pb2.ComputePlanStatus.Value(compute_plan['status']) in [
                    computeplan_pb2.PLAN_STATUS_DONE,
                    computeplan_pb2.PLAN_ACTION_CANCELED,
                    computeplan_pb2.PLAN_STATUS_FAILED]:
                logger.info('Compute plan %s finished with status: %s', compute_plan['key'], compute_plan['status'])
                on_compute_plan_finished.apply_async((channel_name, compute_plan), queue=worker_queue)

    if event_task_status != computetask_pb2.STATUS_TODO:
        return

    if event_pb2.EventKind.Value(event_kind) not in [event_pb2.EVENT_ASSET_CREATED, event_pb2.EVENT_ASSET_UPDATED]:
        return

    if metadata['worker'] != current_worker:
        logger.info(f'Skipping task {asset_key}: worker does not match'
                    f' ({metadata["worker"] } vs {current_worker})')
        return

    with get_orchestrator_client(channel_name) as client:
        task = client.query_task(asset_key)

    task_status = computetask_pb2.ComputeTaskStatus.Value(task["status"])

    if task_status != event_task_status:
        raise ValueError(f'Task {asset_key} status out of sync: task status={task["status"]} '
                         f'!= event status={metadata["status"]}')

    if AsyncResult(asset_key).state != 'PENDING':
        logger.info(f'Skipping task {asset_key}: already exists')
        return

    prepare_task.apply_async(
        (channel_name, task),
        task_id=asset_key,
        queue=worker_queue
    )


def on_model_event(payload):
    worker_queue = f"{settings.ORG_NAME}.worker"
    asset_key = payload["asset_key"]
    event_kind = payload['event_kind']

    logger.info(f'Processing model {asset_key}: type={event_kind}')

    if event_pb2.EventKind.Value(event_kind) == event_pb2.EVENT_ASSET_DISABLED:
        remove_intermediary_models_from_buffer.apply_async([asset_key], queue=worker_queue)


async def on_message(message: aio_pika.IncomingMessage):
    async with message.process(requeue=True):
        payload = json.loads(message.body)
        logger.debug(f"Received payload: {payload}")
        asset_kind = common_pb2.AssetKind.Value(payload['asset_kind'])

        if asset_kind == common_pb2.ASSET_COMPUTE_TASK:
            on_computetask_event(payload)
        elif asset_kind == common_pb2.ASSET_MODEL:
            on_model_event(payload)
        else:
            logger.debug(f"Nothing to do for {payload['asset_kind']} event")


async def consume(loop):
    # Queues are defined by the orchestrator
    queue_name = f"{settings.ORCHESTRATOR_RABBITMQ_AUTH_USER}"

    ssl_options = None
    if settings.ORCHESTRATOR_RABBITMQ_TLS_ENABLED:
        ssl_options = {
            "ca_certs": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CACERT_PATH,
            "certfile": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CERT_PATH,
            "keyfile": settings.ORCHESTRATOR_RABBITMQ_TLS_CLIENT_KEY_PATH,
            "cert_reqs": ssl.CERT_REQUIRED,
        }

    logger.info(f"Attempting to connect to orchestrator RabbitMQ queue {queue_name}")

    connection = await aio_pika.connect_robust(
        host=settings.ORCHESTRATOR_RABBITMQ_HOST,
        port=settings.ORCHESTRATOR_RABBITMQ_PORT,
        login=settings.ORCHESTRATOR_RABBITMQ_AUTH_USER,
        password=settings.ORCHESTRATOR_RABBITMQ_AUTH_PASSWORD,
        ssl=settings.ORCHESTRATOR_RABBITMQ_TLS_ENABLED,
        ssl_options=ssl_options,
        loop=loop
    )

    logger.info(f"Connected to orchestrator RabbitMQ queue {queue_name}")

    # Creating channel
    channel = await connection.channel()    # type: aio_pika.Channel

    # Declaring queue
    queue = await channel.get_queue(queue_name, ensure=True)   # type: aio_pika.Queue

    await queue.consume(on_message)

    return connection


class EventsConfig(AppConfig):
    name = 'events'
    logger.info("starting event app")

    def ready(self):
        with get_event_loop() as loop:

            while True:
                try:
                    connection = loop.run_until_complete(consume(loop))
                except Exception as e:
                    logger.exception(e)
                    time.sleep(5)
                    logger.error('Retry connecting to orchestrator RabbitMQ queue')
                else:
                    break
            try:
                loop.run_forever()
            finally:
                loop.run_until_complete(connection.close())
