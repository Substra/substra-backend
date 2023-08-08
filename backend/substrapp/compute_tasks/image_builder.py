import os
import pathlib
import time
from tempfile import TemporaryDirectory

import structlog
from django.conf import settings

import orchestrator
import substrapp.clients.organization as organization_client
from builder import exceptions
from image_transfer import push_payload
from substrapp.compute_tasks import utils
from substrapp.docker_registry import container_image_exists
from substrapp.exceptions import OrganizationHttpError
from substrapp.utils import get_owner

logger = structlog.get_logger(__name__)

IMAGE_BUILD_TIMEOUT = settings.IMAGE_BUILD_TIMEOUT
IMAGE_BUILD_CHECK_DELAY = settings.IMAGE_BUILD_CHECK_DELAY
REGISTRY = settings.REGISTRY
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR


def wait_for_image_built(function: orchestrator.Function, channel: str) -> None:
    container_image_tag = utils.container_image_tag_from_function(function)
    if function.owner == get_owner():
        attempt = 0
        # with 60 attempts we wait max 2 min with a pending pod
        max_attempts = IMAGE_BUILD_TIMEOUT / IMAGE_BUILD_CHECK_DELAY
        while attempt < max_attempts:
            # Consider relying on celery task success so we can move `container_image_exists` in builder
            if container_image_exists(container_image_tag):
                logger.info("Found existing image", image=container_image_tag)
                return

            attempt += 1
            time.sleep(IMAGE_BUILD_CHECK_DELAY)

        raise exceptions.PodTimeoutError(
            f"Build for function {function.key} didn't complete after {IMAGE_BUILD_TIMEOUT} seconds"
        )
    else:
        # Ask the backend owner of the function if it's available
        logger.info(
            f"Initial function URI {function.function_address.uri}; "
            f"modified URI{function.function_address.uri.replace('file', 'image')}"
        )
        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                function_image_content = organization_client.get(
                    channel=channel,
                    organization_id=function.owner,
                    # TODO create a clean Address for function image
                    url=function.function_address.uri.replace("file", "image"),
                    checksum=None,
                )
            except OrganizationHttpError:
                attempt += 1
                time.sleep(5)

            os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)
            with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
                storage_path = pathlib.Path(tmp_dir) / f"{container_image_tag}.zip"
                storage_path.write_bytes(function_image_content)
                push_payload(storage_path, registry=REGISTRY, secure=False)

            #
            # if exc.status_code == 404:
            #     raise exceptions.CeleryRetryError(f"Function {function.key} was not found
            #     on backend {function.owner}")
            # else:
            #     raise exceptions.CeleryNoRetryError("I've got a bad feeling about this.")
