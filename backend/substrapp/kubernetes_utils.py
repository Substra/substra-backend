import enum
import time
from typing import Tuple

import kubernetes
import structlog
from django.conf import settings

from substrapp.exceptions import PodDeletedError
from substrapp.exceptions import PodError
from substrapp.exceptions import PodReadinessTimeoutError
from substrapp.exceptions import PodTimeoutError
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE
HTTP_CLIENT_TIMEOUT_SECONDS = getattr(settings, "HTTP_CLIENT_TIMEOUT_SECONDS")
RUN_AS_GROUP = settings.COMPUTE_POD_RUN_AS_GROUP
RUN_AS_USER = settings.COMPUTE_POD_RUN_AS_USER
FS_GROUP = settings.COMPUTE_POD_FS_GROUP


class ObjectState(enum.Enum):
    PENDING = enum.auto()
    WAITING = enum.auto()
    RUNNING = enum.auto()
    FAILED = enum.auto()
    COMPLETED = enum.auto()
    UNKNOWN = enum.auto()


def get_pod_security_context(enabled=True, root=False):
    if not enabled or root:
        return None

    return kubernetes.client.V1PodSecurityContext(
        run_as_non_root=True,
        fs_group=int(FS_GROUP),
        run_as_group=int(RUN_AS_GROUP),
        run_as_user=int(RUN_AS_USER),
    )


def get_security_context(enabled=True, root=False, privileged=False, add_capabilities=None):
    if not enabled:
        return None

    if root:
        return kubernetes.client.V1SecurityContext(
            privileged=privileged,
            allow_privilege_escalation=privileged,
            capabilities=kubernetes.client.V1Capabilities(drop=["ALL"], add=add_capabilities),
        )
    else:
        return kubernetes.client.V1SecurityContext(
            privileged=privileged,
            allow_privilege_escalation=privileged,
            capabilities=kubernetes.client.V1Capabilities(drop=["ALL"], add=add_capabilities),
            run_as_non_root=True,
            run_as_group=int(RUN_AS_GROUP),
            run_as_user=int(RUN_AS_USER),
        )


def watch_pod(k8s_client: kubernetes.client.CoreV1Api, name: str):
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
    max_attempts = 5

    # This variable is used to track the current status through retries
    previous_pod_status = None

    while attempt < max_attempts:
        try:
            api_response: kubernetes.client.models.V1Pod = k8s_client.read_namespaced_pod_status(
                name=name, namespace=NAMESPACE
            )
        except kubernetes.client.rest.ApiException as exc:
            logger.warning("Could not retrieve pod status", pod_name=name, exc_info=exc)
            attempt += 1
            time.sleep(0.2)
            continue

        pod_status, (reason, message) = _get_pod_state(api_response.status)

        if pod_status != previous_pod_status:
            previous_pod_status = pod_status
            logger.info(
                "Pod status changed",
                pod_name=name,
                status=pod_status,
                reason=reason,
                message=message,
                attempt=attempt,
                max_attempts=max_attempts,
            )

        if pod_status == ObjectState.COMPLETED:
            return

        if pod_status == ObjectState.FAILED:
            raise PodError(f"Pod {name} terminated with error: {reason}")

        if pod_status == ObjectState.PENDING:
            # Here we basically consume a free retry everytime but we still need to
            # increment attempt because if at some point our pod is stuck in pending state
            # we need to exit this function
            attempt += 1
            time.sleep(2)

        # Here PodInitializing and ContainerCreating are valid reasons to wait more time
        # Other possible reasons include "CrashLoopBackOff", "CreateContainerConfigError",
        # "ErrImagePull", "ImagePullBackOff", "CreateContainerError", "InvalidImageName"
        if (
            pod_status == ObjectState.WAITING
            and reason not in ["PodInitializing", "ContainerCreating"]
            or pod_status == ObjectState.UNKNOWN
        ):
            attempt += 1

        time.sleep(0.2)

    raise PodTimeoutError(f"Pod {name} didn't complete after {max_attempts} attempts")


def _get_pod_state(pod_status: kubernetes.client.models.V1PodStatus) -> Tuple[ObjectState, Tuple[str, str]]:
    """extracts the current pod state from the PodStatus Kubernetes object

    Args:
        pod_status (kubernetes.client.models.V1PodStatus): A Kubernetes PodStatus object

    Returns:
        Tuple[ObjectState, Tuple[str, str]]: A tuple consisting of the pod state and a detailed reason potentially
            explaining this state the reason itself is also a Tuple of the form (reason, detailed message)
    """
    if pod_status.phase in ["Pending"]:
        # On the first query the pod just created and often pending as it is not already scheduled to a node
        return ObjectState.PENDING, ("", "")

    container_statuses = pod_status.init_container_statuses if pod_status.init_container_statuses else []
    container_statuses += pod_status.container_statuses

    completed_containers = 0
    for container in container_statuses:
        container_state: ObjectState = _get_container_state(container)
        if container_state in [ObjectState.RUNNING, ObjectState.WAITING, ObjectState.FAILED]:
            return container_state, _get_container_state_reason(container, container_state)
        if container_state == ObjectState.COMPLETED:
            completed_containers += 1

    if completed_containers == len(container_statuses):
        return ObjectState.COMPLETED, _get_container_state_reason(container, container_state)
    return ObjectState.UNKNOWN, ("", "Could not deduce the pod state from container statuses")


def _get_container_state_reason(
    container_state: kubernetes.client.models.V1ContainerState, current_state: ObjectState
) -> Tuple[str, str]:
    """Extracts the reason and detailed reason message from a ContainerState

    Args:
        container_state (kubernetes.client.models.V1ContainerState): a Kubernetes ContainerState object
        current_state (ObjectState): State of the container

    Returns:
        Tuple[str, str]: a Tuple of the form (reason, detailed message)
    """
    if current_state in [ObjectState.RUNNING, ObjectState.COMPLETED]:
        return "", ""
    if current_state == ObjectState.WAITING:
        return container_state.waiting.reason, container_state.waiting.message
    if current_state == ObjectState.FAILED:
        return container_state.terminated.reason, container_state.terminated.message
    return "", ""


def _get_container_state(container_status: kubernetes.client.models.V1ContainerStatus) -> ObjectState:
    """Extracts the container state from a ContainerStatus Kubernetes object

    Args:
        container_status (kubernetes.client.models.V1ContainerStatus): A ContainerStatus object

    Returns:
        ObjectState: the state of the container
    """
    # Here we need to check if we are in a failed state first since kubernetes will retry
    # we can end up running after a failure
    if container_status.state.terminated:
        if container_status.state.exit_code != 0:
            return ObjectState.FAILED
        else:
            return ObjectState.COMPLETED
    if container_status.state.running:
        return ObjectState.RUNNING
    if container_status.state.waiting:
        return ObjectState.WAITING
    return ObjectState.UNKNOWN


def pod_exists(k8s_client, name: str) -> bool:
    try:
        k8s_client.read_namespaced_pod(name=name, namespace=NAMESPACE)
    except Exception:
        return False
    else:
        return True


def pod_exists_by_label_selector(k8s_client: kubernetes.client.CoreV1Api, label_selector: str) -> bool:
    """Return True if the pod exists, else False.

    :type k8s_client: kubernetes.client.CoreV1Api
    :param k8s_client: A kubernetes client

    :type label_selector: str
    :param label_selector: A comma-delimited label selector, e.g. "label1=value1,label2=value2"

    :rtype: bool
    """
    res = k8s_client.list_namespaced_pod(namespace=NAMESPACE, label_selector=label_selector)
    return len(res.items) > 0


@timeit
def get_pod_logs(k8s_client, name: str, container: str) -> str:
    logs = f"No logs for pod {name}"

    if pod_exists(k8s_client, name):
        try:
            logs = k8s_client.read_namespaced_pod_log(name=name, namespace=NAMESPACE, container=container)
        except Exception:  # nosec
            pass

    return logs


def delete_pod(k8s_client, name: str) -> None:
    if not pod_exists(k8s_client, name):
        return

    # we retrieve the latest pod list version to retrieve only the latest events when watching for pod deletion
    pod_list_resource_version = k8s_client.list_namespaced_pod(namespace=NAMESPACE).metadata.resource_version

    k8s_client.delete_namespaced_pod(
        name=name,
        namespace=NAMESPACE,
        body=kubernetes.client.V1DeleteOptions(propagation_policy="Foreground"),
    )

    # watch for pod deletion
    watch = kubernetes.watch.Watch()
    for event in watch.stream(
        func=k8s_client.list_namespaced_pod, namespace=NAMESPACE, resource_version=pod_list_resource_version
    ):
        if event["type"] == "DELETED" and event["object"].metadata.name == name:
            watch.stop()

    logger.info("Deleted pod", namespace=NAMESPACE, name=name)


def wait_for_pod_readiness(k8s_client, label_selector: str, timeout: int = 60) -> None:

    watch = kubernetes.watch.Watch()

    for event in watch.stream(
        k8s_client.list_namespaced_pod,
        NAMESPACE,
        label_selector=label_selector,
        timeout_seconds=timeout,
    ):
        if event["object"].status.phase == "Running":
            watch.stop()
            return
        if event["type"] == "DELETED":
            watch.stop()
            raise PodDeletedError(f"Pod {label_selector} was deleted before it started.")

    raise PodReadinessTimeoutError(f'Pod {label_selector} failed to reach the "Running" phase after {timeout} seconds.')


def get_pod_by_label_selector(label_selector: str) -> object:

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.list_namespaced_pod(NAMESPACE, label_selector=label_selector)
    if api_response.items:
        pod = api_response.items.pop()
    else:
        raise Exception(f"Could not get pod name {label_selector}")

    return pod


def get_worker_replica_set_scale() -> int:
    """Return the number of workers in the worker replica set"""
    kubernetes.config.load_incluster_config()
    api_instance = kubernetes.client.AppsV1Api()
    resp = api_instance.read_namespaced_stateful_set_scale(settings.WORKER_REPLICA_SET_NAME, NAMESPACE)
    return resp.spec.replicas


def get_volume(
    k8s_client: kubernetes.client.CoreV1Api,
    pod_name: str,
    volume_name: str,
) -> kubernetes.client.V1Volume:

    pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)

    for volume in pod.spec.volumes:
        if volume.name == volume_name:
            return volume
