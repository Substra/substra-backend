import time

import structlog

import orchestrator
from substrapp import exceptions
from substrapp.compute_tasks import utils
from substrapp.docker_registry import container_image_exists

logger = structlog.get_logger(__name__)

MAX_IMAGE_BUILD_TIME = 3 * 60 * 60  # 3 hours
WAITING_TIME = 5  # wait 5 seconds between two queries


def wait_for_image_built(function: orchestrator.Function):
    container_image_tag = utils.container_image_tag_from_function(function)
    if container_image_exists(container_image_tag):
        logger.info("Found existing image", image=container_image_tag)
    else:
        attempt = 0
        # with 60 attempts we wait max 2 min with a pending pod
        max_attempts = MAX_IMAGE_BUILD_TIME / WAITING_TIME

        while attempt < max_attempts:
            if container_image_exists:
                logger.info("Found existing image", image=container_image_tag)
            else:
                attempt += 1
                time.sleep(WAITING_TIME)

        raise exceptions.PodTimeoutError(
            f"Build for function {function.key} didn't complete" f" after {MAX_IMAGE_BUILD_TIME} seconds"
        )
