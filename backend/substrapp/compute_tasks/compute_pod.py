import os

import kubernetes
import structlog
from django.conf import settings

from substrapp.kubernetes_utils import delete_pod
from substrapp.kubernetes_utils import get_pod_security_context
from substrapp.kubernetes_utils import get_security_context

NAMESPACE = settings.NAMESPACE
logger = structlog.get_logger(__name__)


class Label:
    # Keys
    Component = "app.kubernetes.io/component"
    PodType = "substra.ai/pod-type"
    PodName = "substra.ai/pod-name"
    ComputePlanKey = "substra.ai/compute-plan-key"
    FunctionKey = "substra.ai/function-key"
    RandomToken = "substra.ai/random-token"

    # Values
    PodType_ComputeTask = "compute-task"
    Component_Compute = "substra-compute"


class ComputePod:
    def __init__(
        self,
        compute_plan_key: str,
        function_key: str,
    ):
        self.compute_plan_key = compute_plan_key
        self.function_key = function_key

    @property
    def name(self) -> str:
        return f"substra-{self.compute_plan_key[:8]}-compute-{self.function_key[:12]}"

    @staticmethod
    def get_compute_plan_label_selector(compute_plan_key: str) -> str:
        labels = {
            Label.PodType: Label.PodType_ComputeTask,
            Label.Component: Label.Component_Compute,
            Label.ComputePlanKey: compute_plan_key,
        }
        return ",".join({f"{k}={labels[k]}" for k in labels})

    @property
    def label_selector(self) -> str:
        return ",".join({f"{k}={self.labels[k]}" for k in [Label.ComputePlanKey, Label.FunctionKey]})

    @property
    def labels(self) -> dict:
        return {
            Label.PodName: self.name,
            Label.PodType: Label.PodType_ComputeTask,
            Label.Component: Label.Component_Compute,
            Label.ComputePlanKey: self.compute_plan_key,
            Label.FunctionKey: self.function_key,
        }


def create_pod(
    k8s_client,
    compute_pod: ComputePod,
    name,
    image,
    environment,
    volume_mounts,
    volumes,
):
    metadata = kubernetes.client.V1ObjectMeta(name=name, labels=compute_pod.labels)

    container_optional_kwargs = {}

    gpu_volume = []
    gpu_volume_mounts = []
    if settings.COMPUTE_POD_GKE_GPUS_LIMITS > 0:
        container_optional_kwargs["resources"] = kubernetes.client.V1ResourceRequirements(
            limits={"nvidia.com/gpu": str(settings.COMPUTE_POD_GKE_GPUS_LIMITS)}
        )

        # To be able to share the same GPU between different pods in GKE context,
        # we use a "hack" based on misleading the Google Nvidia device plugin with
        # fake gpu devices (/dev/nvidia*), which are just symlinks of the original one.
        #
        # Moreover, it seems that original GPU, which are simlinks, are not automatically mounted once a
        # fake GPU is assigned to a specific pod. To fix that we mount them manually.
        for i in range(settings.COMPUTE_POD_GKE_GPUS_LIMITS):
            gpu_volume_mounts.append(
                {
                    "name": f"nvidia{i}",
                    "mountPath": f"/dev/nvidia{i}",
                    "readOnly": True,
                }
            )
            gpu_volume.append(
                {
                    "name": f"nvidia{i}",
                    "hostPath": {"path": f"/dev/nvidia{i}"},
                }
            )

    container_compute = kubernetes.client.V1Container(
        name=name,
        image=image,
        # Wait until SIGTERM is received, then exit gracefully. See https://stackoverflow.com/a/21882119/1370722
        command=["/bin/sh", "-c", "trap 'trap - TERM; kill -s TERM -- -$$' TERM; tail -f /dev/null & wait; exit 0"],
        args=None,
        volume_mounts=volume_mounts + gpu_volume_mounts,
        security_context=get_security_context(),
        env=[kubernetes.client.V1EnvVar(name=env_name, value=env_value) for env_name, env_value in environment.items()],
        **container_optional_kwargs,
    )

    pod_affinity = kubernetes.client.V1Affinity(
        pod_affinity=kubernetes.client.V1PodAffinity(
            required_during_scheduling_ignored_during_execution=[
                kubernetes.client.V1PodAffinityTerm(
                    label_selector=kubernetes.client.V1LabelSelector(
                        match_expressions=[
                            kubernetes.client.V1LabelSelectorRequirement(
                                key="statefulset.kubernetes.io/pod-name", operator="In", values=[os.getenv("HOSTNAME")]
                            )
                        ]
                    ),
                    topology_key="kubernetes.io/hostname",
                )
            ]
        )
    )

    spec = kubernetes.client.V1PodSpec(
        restart_policy="Never",
        affinity=pod_affinity,
        containers=[container_compute],
        volumes=volumes + gpu_volume,
        security_context=get_pod_security_context(),
        termination_grace_period_seconds=0,
        automount_service_account_token=False,
    )

    pod = kubernetes.client.V1Pod(api_version="v1", kind="Pod", metadata=metadata, spec=spec)

    try:
        logger.info("Creating pod", namespace=NAMESPACE, name=name)
        k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)
    except kubernetes.client.rest.ApiException as e:
        raise Exception(
            f"Error creating pod {NAMESPACE}/{name}. Reason: {e.reason}, status: {e.status}, " f"body: {e.body}"
        ) from None


def delete_compute_plan_pods(compute_plan_key: str) -> None:
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    result = k8s_client.list_namespaced_pod(
        NAMESPACE, label_selector=ComputePod.get_compute_plan_label_selector(compute_plan_key), watch=False
    )

    for pod in result.items:
        delete_pod(k8s_client, pod.metadata.name)
