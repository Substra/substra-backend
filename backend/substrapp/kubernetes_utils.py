import kubernetes
import structlog
import yaml
from django.conf import settings

from substrapp.exceptions import KubernetesError
from substrapp.exceptions import PodDeletedError
from substrapp.exceptions import PodReadinessTimeoutError

logger = structlog.get_logger(__name__)

NAMESPACE = settings.NAMESPACE
RUN_AS_GROUP = settings.COMPUTE_POD_RUN_AS_GROUP
RUN_AS_USER = settings.COMPUTE_POD_RUN_AS_USER
FS_GROUP = settings.COMPUTE_POD_FS_GROUP


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


def get_resources_requirements_from_yaml(
    *,
    yaml_resources: str,
) -> kubernetes.client.V1ResourceRequirements:
    resources_dict = yaml.load(yaml_resources, Loader=yaml.FullLoader)
    return kubernetes.client.V1ResourceRequirements(
        requests=resources_dict["requests"], limits=resources_dict["limits"]
    )


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
