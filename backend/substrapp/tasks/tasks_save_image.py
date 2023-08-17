import os
import pathlib
from tempfile import TemporaryDirectory

import structlog
from django.conf import settings
from django.core.files import File

import orchestrator
from backend.celery import app
from image_transfer import make_payload
from substrapp.compute_tasks import utils
from substrapp.docker_registry import USER_IMAGE_REPOSITORY
from substrapp.models import FunctionImage
from substrapp.tasks.tasks_compute_task import ComputeTask

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR

logger = structlog.get_logger("worker")


@app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    base=ComputeTask,
)
# Ack late and reject on worker lost allows use to
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost
# and https://github.com/celery/celery/issues/5106
def save_image_task(self: ComputeTask, function_serialized: str, channel_name: str, function_key: str) -> None:
    logger.info("Starting save_image_task")
    logger.info(
        f"Parameters: function_serialized {function_serialized}, "
        f"channel_name {channel_name}, function_key {function_key}"
    )
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
