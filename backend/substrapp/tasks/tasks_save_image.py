from __future__ import annotations

import os
import pathlib
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from typing import Any

import structlog

if TYPE_CHECKING:
    from billiard.einfo import ExceptionInfo

from celery import Task
from django.conf import settings
from django.core.files import File

import orchestrator
from backend.celery import app
from image_transfer import make_payload
from substrapp.compute_tasks import utils
from substrapp.docker_registry import USER_IMAGE_REPOSITORY
from substrapp.models import FunctionImage
from substrapp.orchestrator import get_orchestrator_client
from substrapp.tasks.tasks_compute_task import ComputeTask

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR

logger = structlog.get_logger("worker")


class SaveImageTask(Task):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER
    acks_late = True
    reject_on_worker_lost = True
    ignore_result = False

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict[str, Any], einfo: ExceptionInfo
    ) -> None:
        logger.error(exc)
        logger.error(einfo)
        function_key, channel_name = self.get_task_info(args, kwargs)
        with get_orchestrator_client(channel_name) as client:
            client.update_function_status(
                function_key=function_key, action=orchestrator.function_pb2.FUNCTION_ACTION_FAILED
            )

    # Returns (function key, channel)
    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        function = orchestrator.Function.parse_raw(kwargs["function_serialized"])
        channel_name = kwargs["channel_name"]
        return function.key, channel_name

    def on_success(self, retval: dict[str, Any], task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        function_key, channel_name = self.get_task_info(args, kwargs)
        with get_orchestrator_client(channel_name) as client:
            client.update_function_status(
                function_key=function_key, action=orchestrator.function_pb2.FUNCTION_ACTION_READY
            )


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    base=SaveImageTask,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def save_image_task(task: ComputeTask, function_serialized: str, channel_name: str) -> tuple[str, str]:
    logger.info("Starting save_image_task")
    logger.info(f"Parameters: function_serialized {function_serialized}, " f"channel_name {channel_name}")
    # create serialized image
    function = orchestrator.Function.parse_raw(function_serialized)
    container_image_tag = utils.container_image_tag_from_function(function)

    os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)

    logger.info("Serialising the image from the registry")

    with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
        storage_path = pathlib.Path(tmp_dir) / f"{container_image_tag}.zip"
        make_payload(
            zip_file=storage_path,
            docker_images_to_transfer=[f"{USER_IMAGE_REPOSITORY}:{container_image_tag}"],
            registry=REGISTRY,
            secure=False,
        )

        logger.info("Start saving the serialized image")
        # save it
        FunctionImage.objects.create(
            function_id=function.key, file=File(file=storage_path.open(mode="rb"), name="image.zip")
        )
        logger.info("Serialized image saved")

    return function_serialized, channel_name
