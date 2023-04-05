import enum
import time

import kubernetes
import structlog
from django.conf import settings

from substrapp.exceptions import KubernetesError
from substrapp.exceptions import PodDeletedError
from substrapp.exceptions import PodError
from substrapp.exceptions import PodReadinessTimeoutError
from substrapp.exceptions import PodTimeoutError
from substrapp.utils import timeit

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE
HTTP_CLIENT_TIMEOUT_SECONDS = settings.HTTP_CLIENT_TIMEOUT_SECONDS
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


def get_pod_security_context():
    return kubernetes.client.V1PodSecurityContext(
        run_as_non_root=True,
        fs_group=int(FS_GROUP),
        run_as_group=int(RUN_AS_GROUP),
        run_as_user=int(RUN_AS_USER),
    )


def get_security_context(root: bool = False, capabilities: list[str] = None) -> kubernetes.client.V1SecurityContext:
    """
    root:
     - True: force running as root
     - False: disable running as root
    """
    security_context = kubernetes.client.V1SecurityContext(
        privileged=False,
        allow_privilege_escalation=False,
        capabilities=kubernetes.client.V1Capabilities(drop=["ALL"], add=capabilities),
    )

    if root:
        security_context.run_as_non_root = False
        security_context.run_as_group = 0
        security_context.run_as_user = 0
    else:
        security_context.run_as_non_root = True
        security_context.run_as_group = int(RUN_AS_GROUP)
        security_context.run_as_user = int(RUN_AS_USER)

    return security_context


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
    # with 30 attempts we wait max 1 min with a pending pod
    max_attempts = 30

    # This variable is used to track the current status through retries
    previous_pod_status = None

    while attempt < max_attempts:
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
            time.sleep(2)

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


def pod_exists(k8s_client, name: str) -> bool:
    try:
        k8s_client.read_namespaced_pod(name=name, namespace=NAMESPACE)
    except kubernetes.client.ApiException:
        return False
    else:
        return True


def retrieve_pod_status(k8s_client: kubernetes.client.CoreV1Api, pod_name: str) -> kubernetes.client.V1PodStatus:
    pod: kubernetes.client.V1Pod = k8s_client.read_namespaced_pod_status(
        name=pod_name, namespace=NAMESPACE, pretty=True
    )
    return pod.status


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
def get_pod_logs(k8s_client, name: str, container: str, ignore_pod_not_found: bool = False) -> str:
    try:
        return k8s_client.read_namespaced_pod_log(name=name, namespace=NAMESPACE, container=container)
    except kubernetes.client.ApiException as exc:
        if ignore_pod_not_found and exc.reason == "Not Found":
            return f"Pod not found: {NAMESPACE}/{name} ({container})"
        raise


def delete_pod(k8s_client, name: str) -> None:
    # we retrieve the latest pod list version to retrieve only the latest events when watching for pod deletion
    pod_list_resource_version = k8s_client.list_namespaced_pod(namespace=NAMESPACE).metadata.resource_version

    try:
        k8s_client.delete_namespaced_pod(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(propagation_policy="Foreground"),
        )
    except kubernetes.client.exceptions.ApiException as exc:
        if exc.reason == "Not Found":
            return
        raise exc

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


def get_service_node_port(service: str) -> int:
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    try:
        svc: kubernetes.client.V1Service = k8s_client.read_namespaced_service(service, NAMESPACE)
    except kubernetes.client.ApiException as exception:
        raise KubernetesError(f"Failed to retrieve node port service={service}") from exception

    port: kubernetes.client.V1ServicePort = svc.spec.ports[0]

    if not port.node_port:
        raise KubernetesError(
            f"Failed to retrieve node port, nodePort is not set on this port. service={service}, port={port.port}"
        )

    return port.node_port


def execute(pod_name: str, command: list[str]):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    return kubernetes.stream.stream(
        k8s_client.connect_get_namespaced_pod_exec,
        pod_name,
        NAMESPACE,
        # use shell + redirection to ensure stdout/stderr are retrieved in order. Without this,
        # if the program outputs to both stdout and stderr at around the same time,
        # we lose the order of messages.
        command=["/bin/sh", "-c", " ".join(command + ["2>&1"])],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
