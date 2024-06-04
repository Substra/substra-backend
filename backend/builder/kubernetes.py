import enum
import time
from pathlib import Path

import kubernetes
import structlog
from django.conf import settings
from rest_framework import status

from builder.exceptions import PodError
from builder.exceptions import PodTimeoutError
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE
CA_SECRET_NAME = "ca-certificates"  # nosec B105
BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS = settings.BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS
BUILDER_KANIKO_STARTUP_PENDING_STATE_WAIT_SECONDS = settings.BUILDER_KANIKO_STARTUP_PENDING_STATE_WAIT_SECONDS


class ObjectState(enum.Enum):
    PENDING = enum.auto()
    WAITING = enum.auto()
    RUNNING = enum.auto()
    FAILED = enum.auto()
    COMPLETED = enum.auto()
    UNKNOWN = enum.auto()


class PodState:
    def __init__(self, status: ObjectState, reason: str = "", message: str = ""):
        self.status = status
        self.reason = reason
        self.message = message

    def set_reason(self, container_status: kubernetes.client.V1ContainerState) -> None:
        if self.status == ObjectState.WAITING:
            self.reason = container_status.waiting.reason
            self.message = container_status.waiting.message
        if self.status == ObjectState.FAILED:
            self.reason = container_status.terminated.reason
            self.message = container_status.terminated.message


def pod_exists(k8s_client: kubernetes.client.CoreV1Api, name: str) -> bool:
    try:
        k8s_client.read_namespaced_pod(name=name, namespace=NAMESPACE)
    except kubernetes.client.ApiException:
        return False
    else:
        return True


@timeit
def get_pod_logs(
    k8s_client: kubernetes.client.CoreV1Api, name: str, container: str, ignore_pod_not_found: bool = False
) -> str:
    try:
        return k8s_client.read_namespaced_pod_log(name=name, namespace=NAMESPACE, container=container)
    except kubernetes.client.ApiException as exc:
        if ignore_pod_not_found and exc.reason == "Not Found":
            return f"Pod not found: {NAMESPACE}/{name} ({container})"
        if exc.reason == "Bad Request":
            return f"In {NAMESPACE}/{name} \n {str(exc.body)}"
        return f"Unable to get logs for pod {NAMESPACE}/{name} ({container}) \n {str(exc)}"


def watch_pod(k8s_client: kubernetes.client.CoreV1Api, name: str) -> None:
    """Watch a Kubernetes pod status
    It will observe all the containers inside the pod and return when the pod will
    reach the Completed state. If the pod is pending indefinitely or fail, an exception will be raised.
    Args:
        k8s_client (kubernetes.client.CoreV1Api): Kubernetes API client
        name (str): name of the pod to watch
    Raises:
        PodError: this exception is raised if the pod exits with an error
        PodTimeoutError: this exception is raised if the pod does not reach the running state after some time
    """
    attempt = 0
    # with 60 attempts we wait max 2 min with a pending pod
    max_attempts = 60

    # This variable is used to track the current status through retries
    previous_pod_status = None

    while attempt < BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS:
        try:
            api_response = retrieve_pod_status(k8s_client, name)
        except kubernetes.client.ApiException as exc:
            logger.warning("Could not retrieve pod status", pod_name=name, exc_info=exc)
            attempt += 1
            time.sleep(0.2)
            continue

        pod_state = _get_pod_state(api_response)

        if pod_state.status != previous_pod_status:
            previous_pod_status = pod_state.status
            logger.info(
                "Pod status changed",
                pod_name=name,
                status=pod_state.status,
                reason=pod_state.reason,
                message=pod_state.message,
                attempt=attempt,
                max_attempts=max_attempts,
            )

        if pod_state.status == ObjectState.COMPLETED:
            return

        if pod_state.status == ObjectState.FAILED:
            raise PodError(f"Pod {name} terminated with error: {pod_state.reason}")

        if pod_state.status == ObjectState.PENDING:
            # Here we basically consume a free retry everytime but we still need to
            # increment attempt because if at some point our pod is stuck in pending state
            # we need to exit this function
            attempt += 1
            # time.sleep(2)
            time.sleep(BUILDER_KANIKO_STARTUP_PENDING_STATE_WAIT_SECONDS)

        # Here PodInitializing and ContainerCreating are valid reasons to wait more time
        # Other possible reasons include "CrashLoopBackOff", "CreateContainerConfigError",
        # "ErrImagePull", "ImagePullBackOff", "CreateContainerError", "InvalidImageName"
        if (
            pod_state.status == ObjectState.WAITING
            and pod_state.reason not in ["PodInitializing", "ContainerCreating"]
            or pod_state.status == ObjectState.UNKNOWN
        ):
            attempt += 1

        time.sleep(0.2)

    raise PodTimeoutError(f"Pod {name} didn't complete after {max_attempts} attempts")


def retrieve_pod_status(k8s_client: kubernetes.client.CoreV1Api, pod_name: str) -> kubernetes.client.V1PodStatus:
    pod: kubernetes.client.V1Pod = k8s_client.read_namespaced_pod_status(
        name=pod_name, namespace=NAMESPACE, pretty=True
    )
    return pod.status


def _get_pod_state(pod_status: kubernetes.client.V1PodStatus) -> PodState:
    """extracts the current pod state from the PodStatus Kubernetes object
    Args:
        pod_status (kubernetes.client.models.V1PodStatus): A Kubernetes PodStatus object
    """
    if pod_status.phase in ["Pending"]:
        # On the first query the pod just created and often pending as it is not already scheduled to a node
        return PodState(ObjectState.PENDING, pod_status.reason, pod_status.message)

    container_statuses: list[kubernetes.client.V1ContainerStatus] = (
        pod_status.init_container_statuses if pod_status.init_container_statuses else []
    )
    container_statuses += pod_status.container_statuses

    completed_containers = 0
    for container in container_statuses:
        container_state: ObjectState = _get_container_state(container)

        if container_state in [ObjectState.RUNNING, ObjectState.WAITING, ObjectState.FAILED]:
            pod_state = PodState(container_state)
            pod_state.set_reason(container.state)
            return pod_state
        if container_state == ObjectState.COMPLETED:
            completed_containers += 1

    if completed_containers == len(container_statuses):
        return PodState(ObjectState.COMPLETED, "", "pod successfully completed")

    logger.debug("pod status", pod_status=pod_status)
    return PodState(ObjectState.UNKNOWN, "", "Could not deduce the pod state from container statuses")


def _get_container_state(container_status: kubernetes.client.V1ContainerStatus) -> ObjectState:
    """Extracts the container state from a ContainerStatus Kubernetes object
    Args:
        container_status (kubernetes.client.models.V1ContainerStatus): A ContainerStatus object
    Returns:
        ObjectState: the state of the container
    """
    # Here we need to check if we are in a failed state first since kubernetes will retry
    # we can end up running after a failure
    if container_status.state.terminated:
        if container_status.state.terminated.exit_code != 0:
            return ObjectState.FAILED
        else:
            return ObjectState.COMPLETED
    if container_status.state.running:
        return ObjectState.RUNNING
    if container_status.state.waiting:
        return ObjectState.WAITING
    return ObjectState.UNKNOWN


def create_replace_private_ca_secret(k8s_client: kubernetes.client.CoreV1Api):
    cert_file = Path("/etc/ssl/certs/ca-certificates.crt")

    with cert_file.open() as f:
        secret_content = {cert_file.name: f.read()}

    metadata = {"name": CA_SECRET_NAME, "namespace": NAMESPACE}
    body = kubernetes.client.V1Secret(string_data=secret_content, metadata=metadata)
    try:
        k8s_client.create_namespaced_secret(namespace=NAMESPACE, body=body)
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == status.HTTP_409_CONFLICT:
            k8s_client.replace_namespaced_secret(name=CA_SECRET_NAME, namespace=NAMESPACE, body=body)
            return
        raise e
