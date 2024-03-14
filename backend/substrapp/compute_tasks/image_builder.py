import os
import pathlib
from tempfile import TemporaryDirectory

import structlog
from django.conf import settings

import orchestrator
import substrapp.clients.organization as organization_client
from image_transfer import push_payload
from substrapp.compute_tasks import utils

logger = structlog.get_logger(__name__)

IMAGE_BUILD_TIMEOUT = settings.IMAGE_BUILD_TIMEOUT
IMAGE_BUILD_CHECK_DELAY = settings.IMAGE_BUILD_CHECK_DELAY
REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR
USER_IMAGE_REPOSITORY = settings.USER_IMAGE_REPOSITORY


def load_remote_function_image(function: orchestrator.Function, channel: str) -> None:
    # Ask the backend owner of the function if it's available
    container_image_tag = utils.container_image_tag_from_function(function)

    function_image_content = organization_client.get(
        channel=channel,
        organization_id=function.owner,
        url=function.image.uri,
        checksum=function.image.checksum,
    )

    os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)
    with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
        storage_path = pathlib.Path(tmp_dir) / f"{container_image_tag}.zip"
        storage_path.write_bytes(function_image_content)
        push_payload(storage_path, registry=REGISTRY, repository=USER_IMAGE_REPOSITORY, secure=REGISTRY_SCHEME == "https")
