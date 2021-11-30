import datetime
import json
from typing import Dict
from typing import List

import kubernetes
import requests
import structlog
from django.conf import settings

from substrapp.kubernetes_utils import get_pod_by_label_selector

logger = structlog.get_logger(__name__)

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
REGISTRY_PULL_DOMAIN = settings.REGISTRY_PULL_DOMAIN
NAMESPACE = settings.NAMESPACE
REGISTRY_IS_LOCAL = settings.REGISTRY_IS_LOCAL
REGISTRY_SERVICE_NAME = settings.REGISTRY_SERVICE_NAME
HTTP_CLIENT_TIMEOUT_SECONDS = getattr(settings, "HTTP_CLIENT_TIMEOUT_SECONDS")
USER_IMAGE_REPOSITORY = "substrafoundation/user-image"


class ImageNotFoundError(Exception):
    pass


def get_docker_registry_port() -> int:
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    svc = k8s_client.read_namespaced_service(REGISTRY_SERVICE_NAME, NAMESPACE)

    return svc.spec.ports[0].node_port


def get_container_image_name(image_name: str) -> str:
    pull_domain = REGISTRY_PULL_DOMAIN

    if REGISTRY_IS_LOCAL:
        try:
            registry_port = get_docker_registry_port()
        except Exception as e:
            raise Exception("Failed to retrieve docker registry node port") from e
        pull_domain += f":{registry_port}"

    return f"{pull_domain}/{USER_IMAGE_REPOSITORY}:{image_name}"


def delete_container_image(image_tag: str) -> None:
    logger.info("Deleting image", image=image_tag)

    try:
        response = requests.get(
            f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{image_tag}",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
        )

        if response.status_code != requests.status_codes.codes.ok:
            return

        digest = response.headers["Docker-Content-Digest"]

        response = requests.delete(
            f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{digest}",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
        )
        if response.status_code != requests.status_codes.codes.accepted:
            return

    except Exception as e:
        logger.exception(e)


def container_image_exists(image_name: str) -> bool:
    try:
        get_container_image(image_name)
    except ImageNotFoundError:
        return False
    else:
        return True


def get_container_image(image_name: str) -> Dict:
    response = requests.get(
        f"{REGISTRY_SCHEME}://{REGISTRY}/v2/{USER_IMAGE_REPOSITORY}/manifests/{image_name}",
        headers={"Accept": "application/json"},
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFoundError(f"Error when querying docker-registry, status code: {response.status_code}")

    return response.json()


def get_container_images() -> List[Dict]:
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


def fetch_old_algo_image_names(max_duration: int) -> List[str]:
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
