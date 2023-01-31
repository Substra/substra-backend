import datetime
import json

import kubernetes
import requests
import structlog
from django.conf import settings

from substrapp.exceptions import ImageDeletionError
from substrapp.kubernetes_utils import get_pod_by_label_selector
from substrapp.kubernetes_utils import get_service_node_port

logger = structlog.get_logger(__name__)

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
REGISTRY_PULL_DOMAIN = settings.REGISTRY_PULL_DOMAIN
NAMESPACE = settings.NAMESPACE
REGISTRY_IS_LOCAL = settings.REGISTRY_IS_LOCAL
REGISTRY_SERVICE_NAME = settings.REGISTRY_SERVICE_NAME
HTTP_CLIENT_TIMEOUT_SECONDS = settings.HTTP_CLIENT_TIMEOUT_SECONDS
USER_IMAGE_REPOSITORY = "substrafoundation/user-image"


class ImageNotFoundError(Exception):
    pass


class RetrieveDigestError(Exception):
    pass


class ImageDigestNotFound(RetrieveDigestError):
    pass


def get_container_image_name(image_name: str) -> str:
    pull_domain = REGISTRY_PULL_DOMAIN

    if REGISTRY_IS_LOCAL:
        registry_port = get_service_node_port(REGISTRY_SERVICE_NAME)
        pull_domain += f":{registry_port}"

    return f"{pull_domain}/{USER_IMAGE_REPOSITORY}:{image_name}"


def delete_container_image_safe(image_tag: str) -> None:
    """deletes a container image from the docker registry but will fail silently"""
    try:
        delete_container_image(image_tag)
    except ImageDeletionError as exception:
        logger.exception("Deletion of the container image failed", exc=exception, image_tag=image_tag)


def delete_container_image(image_tag: str) -> None:
    """deletes a container image from the docker registry"""
    logger.info("Deleting image", image=image_tag)
    try:
        digest = _retrieve_image_digest(image_tag)
        response = requests.delete(
            f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{digest}",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
        )
    except ImageDigestNotFound:
        # Image does not exist
        return
    except (requests.exceptions.RequestException, RetrieveDigestError) as exception:
        raise ImageDeletionError(image_tag=image_tag) from exception

    if response.status_code != requests.status_codes.codes.accepted:
        raise ImageDeletionError(image_tag=image_tag, status_code=response.status_code)


def _retrieve_image_digest(image_tag: str) -> str:
    try:
        response = requests.get(
            f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{image_tag}",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
        )

    except requests.exceptions.RequestException as exception:
        raise RetrieveDigestError() from exception

    if response.status_code == 404:
        raise ImageDigestNotFound()

    if response.status_code != requests.status_codes.codes.ok:
        raise RetrieveDigestError()

    return response.headers["Docker-Content-Digest"]


def container_image_exists(image_name: str) -> bool:
    try:
        get_container_image(image_name)
    except ImageNotFoundError:
        return False
    else:
        return True


def get_container_image(image_name: str) -> dict:
    response = requests.get(
        f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{image_name}",
        headers={"Accept": "application/json"},
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFoundError(f"Error when querying docker-registry, status code: {response.status_code}")

    return response.json()


def get_container_images() -> list[dict]:
    response = requests.get(
        f"{REGISTRY_SCHEME}://{REGISTRY}/v2/_catalog",
        headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    res = response.json()

    for repository in res["repositories"]:
        # get only user-image repo, images built by substra-backend
        if repository == USER_IMAGE_REPOSITORY:
            response = requests.get(
                f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{repository}/tags/list",
                headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
                timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
            )

            response.raise_for_status()
            return response.json()

    return None


def fetch_old_function_image_names(max_duration: int) -> list[str]:
    logger.info("Fetch old image names", max_duration=f"{max_duration}s")

    images = get_container_images()

    old_images = []
    if images:
        for image in images["tags"]:
            response = requests.get(
                f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{image}",
                timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            # take the most recent date as creation date
            created_date = max(
                [
                    datetime.datetime.strptime(
                        json.loads(e["v1Compatibility"])["created"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
                    )
                    for e in response.json()["history"]
                ]
            )

            if (datetime.datetime.now() - created_date).total_seconds() >= max_duration:
                old_images.append(image["name"])

    return old_images


def run_garbage_collector() -> None:
    logger.info("Launch garbage collect on docker-registry")

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()
    pod = get_pod_by_label_selector("app=docker-registry")
    pod_name = pod.metadata.name
    exec_command = ["/bin/sh", "-c", "/bin/registry garbage-collect /etc/docker/registry/config.yml 2>&1"]

    resp = kubernetes.stream.stream(
        k8s_client.connect_get_namespaced_pod_exec,
        pod_name,
        NAMESPACE,
        command=exec_command,
        stderr=True,
        stdin=True,
        stdout=True,
        tty=True,
        _preload_content=False,
    )

    logs = []

    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            lines = resp.read_stdout()
            for line in filter(None, lines.split("\n")):
                logs.append(line)
    else:
        logger.info(logs[-1])

    returncode = resp.returncode
    resp.close()

    if returncode != 0:
        raise Exception(f"Error running docker-registry garbage collector (exited with code {returncode})")
