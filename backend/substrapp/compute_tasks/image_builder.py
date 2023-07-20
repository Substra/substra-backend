import time

import structlog
from django.conf import settings

import orchestrator
from builder import exceptions
from substrapp.compute_tasks import utils
from substrapp.docker_registry import container_image_exists

logger = structlog.get_logger(__name__)

IMAGE_BUILD_TIMEOUT = settings.IMAGE_BUILD_TIMEOUT
IMAGE_BUILD_CHECK_DELAY = settings.IMAGE_BUILD_CHECK_DELAY


def wait_for_image_built(function: orchestrator.Function) -> None:
    container_image_tag = utils.container_image_tag_from_function(function)
    attempt = 0
    # with 60 attempts we wait max 2 min with a pending pod
    max_attempts = IMAGE_BUILD_TIMEOUT / IMAGE_BUILD_CHECK_DELAY
    while (
        attempt < max_attempts
    ):  # Consider relying on celery task success so we can move `container_image_exists` in builder
        if container_image_exists(container_image_tag):
            logger.info("Found existing image", image=container_image_tag)
            return

        attempt += 1
        time.sleep(IMAGE_BUILD_CHECK_DELAY)

    raise exceptions.PodTimeoutError(
        f"Build for function {function.key} didn't complete after {IMAGE_BUILD_TIMEOUT} seconds"
    )
