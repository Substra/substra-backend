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
    AlgoKey = "substra.ai/algo-key"
    MetricKey = "substra.ai/testtuple-eval-metric-key"
    RandomToken = "substra.ai/random-token"

    # Values
    PodType_ComputeTask = "compute-task"
    Component_Compute = "substra-compute"


class ComputePod:
    compute_plan_key: str = None
    algo_key: str = None
    metric_key: str = None  # only if this is a testtuple eval pod

    def __init__(
        self,
        compute_plan_key: str,
        algo_key: str,
        metric_key: str,
    ):
        self.compute_plan_key = compute_plan_key
        self.algo_key = algo_key
        self.metric_key = metric_key

    @property
    def is_testtuple_eval(self) -> bool:
        return self.metric_key is not None

    @property
    def name(self) -> str:
        if self.is_testtuple_eval:
            return f"substra-{self.compute_plan_key[:8]}-eval-{self.metric_key[:8]}"
        else:
            return f"substra-{self.compute_plan_key[:8]}-compute-{self.algo_key[:8]}"

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
        return ",".join({f"{k}={self.labels[k]}" for k in [Label.ComputePlanKey, Label.AlgoKey, Label.MetricKey]})

    @property
    def labels(self) -> object:
        return {
            Label.PodName: self.name,
            Label.PodType: Label.PodType_ComputeTask,
            Label.Component: Label.Component_Compute,
            Label.ComputePlanKey: self.compute_plan_key,
            Label.AlgoKey: self.algo_key or "",
            Label.MetricKey: self.metric_key or "",
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
    if settings.COMPUTE_POD_GKE_GPUS_LIMITS > 0:
        container_optional_kwargs["resources"] = kubernetes.client.V1ResourceRequirements(
            limits={"nvidia.com/gpu": str(settings.COMPUTE_POD_GKE_GPUS_LIMITS)}
        )

    container_compute = kubernetes.client.V1Container(
        name=name,
        image=image,
        # Wait until SIGTERM is received, then exit gracefully. See https://stackoverflow.com/a/21882119/1370722
        command=["/bin/sh", "-c", "trap 'trap - TERM; kill -s TERM -- -$$' TERM; tail -f /dev/null & wait; exit 0"],
        args=None,
        volume_mounts=volume_mounts,
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
        volumes=volumes,
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
