from __future__ import annotations

import os
import pathlib
from tempfile import TemporaryDirectory
from typing import Any

import structlog
from django.conf import settings
from django.core.files import File
from django.urls import reverse

import orchestrator
from api.models import Function as ApiFunction
from backend.celery import app
from image_transfer import make_payload
from substrapp.compute_tasks import utils
from substrapp.docker_registry import USER_IMAGE_REPOSITORY
from substrapp.models import FailedAssetKind
from substrapp.models import FunctionImage
from substrapp.orchestrator import get_orchestrator_client
from substrapp.tasks.task import FailableTask

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR

logger = structlog.get_logger("worker")


class SaveImageTask(FailableTask):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER
    acks_late = True
    reject_on_worker_lost = True
    ignore_result = False

    asset_type = FailedAssetKind.FAILED_ASSET_FUNCTION

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    # Returns (function key, channel)
    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        function = orchestrator.Function.parse_raw(kwargs["function_serialized"])
        channel_name = kwargs["channel_name"]
        return function.key, channel_name

    # Celery does not provide unpacked arguments, we are doing it in `get_task_info`
    def on_success(self, retval: tuple[str, str], task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        orc_update_function_param, channel_name = retval

        with get_orchestrator_client(channel_name) as client:
            client.update_function(orc_update_function_param)
            client.update_function_status(
                function_key=orc_update_function_param["key"], action=orchestrator.function_pb2.FUNCTION_ACTION_READY
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
def save_image_task(task: SaveImageTask, function_serialized: str, channel_name: str) -> tuple[str, str]:
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
        image = FunctionImage.objects.create(
            function_id=function.key, file=File(file=storage_path.open(mode="rb"), name="image.zip")
        )
        # update APIFunction image-related fields
        api_function = ApiFunction.objects.get(key=function.key)
        # TODO get full url cf https://github.com/Substra/substra-backend/backend/api/serializers/function.py#L66
        api_function.image_address = settings.DEFAULT_DOMAIN + reverse("api:function-image", args=[function.key])
        api_function.image_checksum = image.checksum
        api_function.save()

        logger.info("Serialized image saved")

        orc_update_function_param = {
            "key": str(api_function.key),
            # TODO find a way to propagate the name or make it optional at update
            "name": api_function.name,
            "image": {
                "checksum": api_function.image_checksum,
                # TODO check url
                "storage_address": api_function.image_address,
            },
        }

        return orc_update_function_param, channel_name
