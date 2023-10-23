import os
import pathlib
import time
from tempfile import TemporaryDirectory

import structlog
from django.conf import settings

import orchestrator
import substrapp.clients.organization as organization_client
from api.models import Function as ApiFunction
from builder import exceptions
from image_transfer import push_payload
from substrapp.compute_tasks import utils

logger = structlog.get_logger(__name__)

IMAGE_BUILD_TIMEOUT = settings.IMAGE_BUILD_TIMEOUT
IMAGE_BUILD_CHECK_DELAY = settings.IMAGE_BUILD_CHECK_DELAY
REGISTRY = settings.REGISTRY
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR


def wait_for_image_built(function: orchestrator.Function, channel: str) -> None:
    api_function = ApiFunction.objects.get(key=function.key)

    attempt = 0
    # with 60 attempts we wait max 2 min with a pending pod
    max_attempts = IMAGE_BUILD_TIMEOUT / IMAGE_BUILD_CHECK_DELAY
    while attempt < max_attempts:
        if api_function.status == ApiFunction.Status.FUNCTION_STATUS_READY:
            return
        attempt += 1
        time.sleep(IMAGE_BUILD_CHECK_DELAY)
        api_function.refresh_from_db()

    raise exceptions.PodTimeoutError(
        f"Build for function {function.key} didn't complete after {IMAGE_BUILD_TIMEOUT} seconds"
    )


def load_remote_function_image(function: orchestrator.Function, channel: str) -> None:
    container_image_tag = utils.container_image_tag_from_function(function)
    # Ask the backend owner of the function if it's available

    # Necessary to query the DB again to get an updated Function object
    # Else the image URI is not available
    api_function = ApiFunction.objects.get(key=function.key)

    function_image_content = organization_client.get(
        channel=channel,
        organization_id=function.owner,
        url=function.image.uri,
        checksum=function.image.checksum,
        # url=api_function.image_address,
        # checksum=api_function.image_checksum,
    )

    os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)
    with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
        storage_path = pathlib.Path(tmp_dir) / f"{container_image_tag}.zip"
        storage_path.write_bytes(function_image_content)
        push_payload(storage_path, registry=REGISTRY, secure=False)
