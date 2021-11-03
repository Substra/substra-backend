import kubernetes
import structlog
import time

from django.conf import settings
from substrapp.utils import timeit
from substrapp.exceptions import PodError, PodTimeoutError, PodDeletedError, PodReadinessTimeoutError

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE
HTTP_CLIENT_TIMEOUT_SECONDS = getattr(settings, "HTTP_CLIENT_TIMEOUT_SECONDS")
RUN_AS_GROUP = settings.COMPUTE_POD_RUN_AS_GROUP
RUN_AS_USER = settings.COMPUTE_POD_RUN_AS_USER
FS_GROUP = settings.COMPUTE_POD_FS_GROUP


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


def watch_pod(k8s_client, name: str, watch_init_container=False):
    finished = False
    attempt = 0
    max_attempts = 5 + (5 if watch_init_container else 0)
    error = None
    watch_container = not watch_init_container

    log = logger.bind(
        pod_name=name,
    )

    log.info("Waiting for pod")

    pod_status = None

    while (not finished) and (attempt < max_attempts):
        try:
            api_response = k8s_client.read_namespaced_pod_status(name=name, namespace=NAMESPACE, pretty=True)

            if api_response.status.phase != pod_status:
                pod_status = api_response.status.phase
                log.info('Status for pod', status=api_response.status.phase)

            # Handle pod error not linked with containers
            if api_response.status.phase == "Failed" or (
                api_response.status.reason and "Evicted" in api_response.status.reason
            ):

                if api_response.status.reason:
                    error = api_response.status.reason
                else:
                    error = f"Pod phase : {api_response.status.phase}"

                log.error('Status for pod', status=api_response.status.phase.lower())
                finished = True
                continue

            if watch_init_container:
                if api_response.status.init_container_statuses:
                    for init_container in api_response.status.init_container_statuses:
                        state = init_container.state
                        if state.terminated:
                            # TODO: support multiple init containers
                            if state.terminated.exit_code != 0:
                                finished = True
                                error = "InitContainer: " + _get_pod_error(state.terminated)
                            else:
                                watch_container = True  # Init container is ready
                        else:
                            if state.waiting and state.waiting.reason not in [
                                "PodInitializing",
                                "ContainerCreating",
                            ]:
                                error = "InitContainer: " + _get_pod_error(state.waiting)
                                attempt += 1
                                log.error(
                                    'InitContainer waiting status',
                                    attempt=attempt,
                                    max_attempts=max_attempts,
                                    state=state.waiting.message,
                                )

            if watch_container:
                if api_response.status.container_statuses:
                    for container in api_response.status.container_statuses:
                        state = container.state
                        if state.terminated:
                            finished = True
                            error = None
                            if state.terminated.exit_code != 0:
                                error = _get_pod_error(state.terminated)

                        else:
                            # {"ContainerCreating", "CrashLoopBackOff", "CreateContainerConfigError",
                            #  "ErrImagePull", "ImagePullBackOff", "CreateContainerError", "InvalidImageName"}
                            if state.waiting and state.waiting.reason not in [
                                "PodInitializing",
                                "ContainerCreating",
                            ]:
                                error = _get_pod_error(state.waiting)
                                attempt += 1
                                log.error(
                                    'Container waiting status',
                                    attempt=attempt,
                                    max_attempts=max_attempts,
                                    state=state.waiting.message,
                                )

            if not finished:
                time.sleep(0.2)

        except Exception as e:
            attempt += 1
            log.error('Could not get pod status', exc_info=e, attempt=attempt, max_attempts=max_attempts)

    if error is not None:
        raise PodError(f"Pod {name} terminated with error: {error}")

    if not finished:
        raise PodTimeoutError(f"Pod {name} didn't complete after {max_attempts} attempts")


def _get_pod_error(state) -> str:
    error = state.reason
    if state.message is not None:
        error += f" ({state.message})"
    return error


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
        except Exception:
            pass

    return logs


def delete_pod(k8s_client, name: str) -> None:
    if not pod_exists(k8s_client, name):
        return

    # we retrieve the latest pod list version to retrieve only the latest events when watching for pod deletion
    pod_list_ressource_version = k8s_client.list_namespaced_pod(namespace=NAMESPACE).metadata.resource_version

    k8s_client.delete_namespaced_pod(
        name=name,
        namespace=NAMESPACE,
        body=kubernetes.client.V1DeleteOptions(propagation_policy="Foreground"),
    )

    # watch for pod deletion
    watch = kubernetes.watch.Watch()
    for event in watch.stream(
        func=k8s_client.list_namespaced_pod,
        namespace=NAMESPACE,
        resource_version=pod_list_ressource_version
    ):
        if event['type'] == 'DELETED' and event['object'].metadata.name == name:
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
        volume_name: str,) -> kubernetes.client.V1Volume:

    pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)

    for volume in pod.spec.volumes:
        if volume.name == volume_name:
            return volume

    return None
