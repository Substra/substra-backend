import base64
import json
import typing
from pathlib import Path

import kubernetes
import requests
import structlog
from django.conf import settings

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
USER_IMAGE_REPOSITORY = "substra/user-image"


class ImageNotFoundError(Exception):
    pass


class RetrieveDigestError(Exception):
    pass


class ImageDigestNotFound(RetrieveDigestError):
    pass


class DockerAuthDict(typing.TypedDict):
    username: str
    password: str
    auth: str


def get_registry_auth() -> typing.Optional[DockerAuthDict]:
    config_path = Path("/.docker/config.json")
    if config_path.is_file():
        with config_path.open("r") as f:
            content = json.load(f)
            return content.get("auths", {}).get(f"{settings.REGISTRY}", None)

    return None


def get_request_docker_api(
    path: str, header_accept: str = "application/vnd.docker.distribution.manifest.v2+json"
) -> dict:
    headers = {"Accept": header_accept}

    auth_content = get_registry_auth()

    if auth_content:
        username = auth_content["username"]
        password = auth_content["password"]
        headers["Authorization"] = "Basic " + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")

    response = requests.get(
        f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{path}",
        headers=headers,
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
        # TODO: add verification before release
        verify=False,  # nosec B501
    )

    response.raise_for_status()

    return response.json()


def get_container_image_name(image_name: str) -> str:
    pull_domain = REGISTRY_PULL_DOMAIN

    if REGISTRY_IS_LOCAL:
        registry_port = get_service_node_port(REGISTRY_SERVICE_NAME)
        pull_domain += f":{registry_port}"

    return f"{pull_domain}/{USER_IMAGE_REPOSITORY}:{image_name}"


def get_entrypoint(image_tag: str) -> str:
    manifest = get_container_manifest(image_tag)
    blob = get_container_blob(manifest["config"]["digest"])

    return blob["config"]["Entrypoint"]


def get_container_manifest(image_name: str) -> dict:
    try:
        return get_request_docker_api(
            f"{USER_IMAGE_REPOSITORY}/manifests/{image_name}",
        )
    except requests.exceptions.HTTPError as err:
        raise ImageNotFoundError(f"Error when querying docker-registry, status code: {err.response.status_code}")


def get_container_blob(digest: str) -> dict:
    return get_request_docker_api(
        f"{USER_IMAGE_REPOSITORY}/blobs/{digest}",
    )


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
