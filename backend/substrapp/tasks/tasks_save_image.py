from __future__ import annotations

import os
import pathlib
from tempfile import TemporaryDirectory
from typing import Any

import structlog
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.files import File
from django.urls import reverse

import image_transfer
import orchestrator
from api.models import Function as ApiFunction
from backend.celery import app
from builder.exceptions import BuildRetryError
from orchestrator import get_orchestrator_client
from substrapp.compute_tasks import utils
from substrapp.compute_tasks.errors import CeleryNoRetryError
from substrapp.compute_tasks.errors import CeleryRetryError
from substrapp.docker_registry import USER_IMAGE_REPOSITORY
from substrapp.docker_registry import RegistryPreconditionFailedException
from substrapp.models import FailedAssetKind
from substrapp.models import FunctionImage
from substrapp.tasks.task import FailableTask
from substrapp.utils import Timer

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR
IMAGE_SAVING_TIMEOUT_SECONDS = settings.IMAGE_SAVING_TIMEOUT_SECONDS

logger = structlog.get_logger("worker")


class SaveImageTask(FailableTask):
    autoretry_for = settings.CELERY_TASK_AUTORETRY_FOR
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = settings.CELERY_TASK_RETRY_BACKOFF
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = settings.CELERY_TASK_RETRY_JITTER
    soft_time_limit = IMAGE_SAVING_TIMEOUT_SECONDS
    acks_late = True
    reject_on_worker_lost = True
    ignore_result = False

    asset_type = FailedAssetKind.FAILED_ASSET_FUNCTION
    timer: Timer

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        self.timer = Timer()
        self.timer.start()

    @property
    def attempt(self) -> int:
        return self.request.retries + 1  # type: ignore

    # Returns (function key, channel)
    def get_task_info(self, args: tuple, kwargs: dict) -> tuple[str, str]:
        function = orchestrator.Function.model_validate_json(kwargs["function_serialized"])
        channel_name = kwargs["channel_name"]
        return function.key, channel_name

    # Celery does not provide unpacked arguments, we are doing it in `get_task_info`
    def on_success(self, retval: tuple[dict, str], task_id: str, args: tuple, kwargs: dict[str, Any]) -> None:
        orc_update_function_param, channel_name = retval
        function_key = orc_update_function_param["key"]
        with get_orchestrator_client(channel_name) as client:
            client.update_function(orc_update_function_param)
            client.update_function_status(
                function_key=function_key, action=orchestrator.function_pb2.FUNCTION_ACTION_READY
            )
            client.register_profiling_step(
                asset_key=function_key,
                duration=self.timer.stop(),
                step=orchestrator.FunctionProfilingStep.SAVE_FUNCTION,
            )


def save_image(function_serialized: str, channel_name: str) -> dict:
    logger.info("Starting save_image")
    logger.info(f"Parameters: function_serialized {function_serialized}, " f"channel_name {channel_name}")
    try:
        # create serialized image
        function = orchestrator.Function.model_validate_json(function_serialized)
        container_image_tag = utils.container_image_tag_from_function(function)

        os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)

        logger.info("Serialising the image from the registry")

        with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
            storage_path = pathlib.Path(tmp_dir) / f"{container_image_tag}.zip"
            try:
                image_transfer.make_payload(
                    zip_file=storage_path,
                    docker_images_to_transfer=[f"{USER_IMAGE_REPOSITORY}:{container_image_tag}"],
                    registry=REGISTRY,
                    secure=REGISTRY_SCHEME == "https",
                )
            except RegistryPreconditionFailedException as e:
                raise BuildRetryError(
                    f"The image associated with the function {function.key} was built successfully "
                    f"but did not pass the security checks; "
                    "please contact an Harbor administrator to ensure that the image was scanned, "
                    "and get more information about the CVE."
                ) from e

            logger.info("Start saving the serialized image")
            # save it
            image = FunctionImage.objects.create(
                function_id=function.key, file=File(file=storage_path.open(mode="rb"), name="image.zip")
            )
            # update APIFunction image-related fields
            api_function = ApiFunction.objects.get(key=function.key)
            # TODO get full url cf https://github.com/Substra/substra-backend/backend/api/serializers/function.py#L66
            api_function.image_address = settings.DEFAULT_DOMAIN + reverse(
                "api:function_permissions-image", args=[function.key]
            )
            api_function.image_checksum = image.checksum
            api_function.save()

            logger.info("Serialized image saved")

            orc_update_function_param = {
                "key": str(api_function.key),
                # TODO find a way to propagate the name or make it optional at update
                "name": api_function.name,
                "image": {
                    "checksum": api_function.image_checksum,
                    "storage_address": api_function.image_address,
                },
            }

            return orc_update_function_param
    except SoftTimeLimitExceeded as e:
        raise CeleryRetryError from e
    except Exception:
        raise


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
def save_image_task(task: SaveImageTask, function_serialized: str, channel_name: str) -> tuple[dict, str]:
    try:
        orc_update_function_param = save_image(function_serialized, channel_name)
    except BuildRetryError:
        raise
    except Exception as e:
        raise CeleryNoRetryError from e
    return orc_update_function_param, channel_name
