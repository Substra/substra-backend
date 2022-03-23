import json
import os
from tempfile import TemporaryDirectory
from typing import List

import kubernetes
import structlog
from django.conf import settings

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.clients import node as node_client
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks.compute_pod import Label
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.volumes import get_docker_cache_pvc_name
from substrapp.compute_tasks.volumes import get_worker_subtuple_pvc_name
from substrapp.docker_registry import USER_IMAGE_REPOSITORY
from substrapp.docker_registry import container_image_exists
from substrapp.kubernetes_utils import delete_pod
from substrapp.kubernetes_utils import get_pod_logs
from substrapp.kubernetes_utils import get_security_context
from substrapp.kubernetes_utils import pod_exists
from substrapp.kubernetes_utils import watch_pod
from substrapp.lock_local import lock_resource
from substrapp.models.image_entrypoint import ImageEntrypoint
from substrapp.utils import timeit
from substrapp.utils import uncompress_content

logger = structlog.get_logger(__name__)

REGISTRY = settings.REGISTRY
REGISTRY_SCHEME = settings.REGISTRY_SCHEME
NAMESPACE = settings.NAMESPACE
KANIKO_MIRROR = settings.TASK["KANIKO_MIRROR"]
KANIKO_IMAGE = settings.TASK["KANIKO_IMAGE"]
KANIKO_DOCKER_CONFIG_SECRET_NAME = settings.TASK["KANIKO_DOCKER_CONFIG_SECRET_NAME"]
CELERY_WORKER_CONCURRENCY = settings.CELERY_WORKER_CONCURRENCY
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR
MAX_IMAGE_BUILD_TIME = 3 * 60 * 60  # 3 hours


def build_images(ctx: Context) -> None:
    # Algo
    _build_image_if_missing(
        ctx,
        ctx.algo_image_tag,
        ctx.algo_key,
        ctx.algo["algorithm"]["storage_address"],
        ctx.algo["owner"],
        ctx.algo["algorithm"]["checksum"],
    )

    # Metrics
    if ctx.task_category == computetask_pb2.TASK_TEST:
        for metric_key, metric_image_tag in ctx.metrics_image_tags.items():
            _build_image_if_missing(
                ctx,
                metric_image_tag,
                metric_key,
                ctx.metrics[metric_key]["address"]["storage_address"],
                ctx.metrics[metric_key]["owner"],
                ctx.metrics[metric_key]["address"]["checksum"],
            )


def _build_image_if_missing(
    ctx: Context, image_tag: str, asset_key: str, asset_storage_address: str, asset_owner: str, asset_checksum: str
) -> None:
    """
    Build the container image and the ImageEntryPoint entry if they don't exist already
    """

    with lock_resource("image-build", image_tag, ttl=MAX_IMAGE_BUILD_TIME, timeout=MAX_IMAGE_BUILD_TIME):
        if container_image_exists(image_tag):
            logger.info("Reusing existing image", image=image_tag)
        else:
            _build_asset_image(
                ctx,
                image_tag,
                asset_key,
                asset_storage_address,
                asset_owner,
                asset_checksum,
            )


def _build_asset_image(
    ctx: Context,
    image_tag: str,
    asset_key: str,
    asset_storage_address: str,
    asset_owner: str,
    asset_checksum: str,
) -> None:
    """
    Build an asset's container image. Perform multiple steps:
    1. Download the asset (algo or metric) using the provided asset storage_address/owner. Verify its checksum and
       uncompress the data to a temporary folder.
    2. Extract the ENTRYPOINT from the Dockerfile.
    3. Build the container image using Kaniko.
    4. Save the ENTRYPOINT to the DB
    """

    os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)

    with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
        # Download source
        content = node_client.get(ctx.channel_name, asset_owner, asset_storage_address, asset_checksum)
        uncompress_content(content, tmp_dir)

        # Extract ENTRYPOINT from Dockerfile
        entrypoint = _get_entrypoint_from_dockerfile(tmp_dir)

        # Build image
        _build_container_image(tmp_dir, image_tag, ctx)

        # Save entrypoint to DB if the image build was successful
        ImageEntrypoint.objects.get_or_create(asset_key=asset_key, entrypoint_json=json.dumps(entrypoint))


def _get_entrypoint_from_dockerfile(dockerfile_dir: str) -> List[str]:
    """
    Get entrypoint from ENTRYPOINT in the Dockerfile.

    This is necessary because the user algo can have arbitrary names, ie; "myalgo.py".

    Example:
        ENTRYPOINT ["python3", "myalgo.py"]
    """
    dockerfile_path = f"{dockerfile_dir}/Dockerfile"

    with open(dockerfile_path, "r") as file:
        for line in file:
            if line.startswith("ENTRYPOINT"):
                try:
                    res = json.loads(line[len("ENTRYPOINT") :])
                except json.JSONDecodeError:
                    res = None

                if not isinstance(res, list):
                    raise compute_task_errors.BuildError(
                        "Invalid ENTRYPOINT in algo/metric Dockerfile. You must use the exec form in your Dockerfile. "
                        "See https://docs.docker.com/engine/reference/builder/#entrypoint"
                    )
                return res

    raise compute_task_errors.BuildError("Invalid Dockerfile: Cannot find ENTRYPOINT")


# TODO: '_build_container_image' is too complex, consider refactoring
@timeit
def _build_container_image(path: str, tag: str, ctx: Context) -> None:  # noqa: C901

    _assert_dockerfile(path)

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    pod_name = f'kaniko-{tag.split("/")[-1].replace("_", "-")}'

    dockerfile_fullpath = os.path.join(path, "Dockerfile")

    dockerfile_mount_subpath = path.split("/subtuple/")[-1]

    image = KANIKO_IMAGE
    command = None
    mount_path_dockerfile = path

    args = [
        f"--dockerfile={dockerfile_fullpath}",
        f"--context=dir://{path}",
        f"--destination={REGISTRY}/{USER_IMAGE_REPOSITORY}:{tag}",
        "--cache=true",
        "--log-timestamp=true",
        "--snapshotMode=redo",
        "--push-retry=3",
        "--cache-copy-layers",
        "--single-snapshot",
        "--log-format=text",
        f"--verbosity={('debug' if settings.LOG_LEVEL == 'DEBUG' else 'info')}",
    ]

    if REGISTRY_SCHEME == "http":
        args.append("--insecure")

    if KANIKO_MIRROR:
        args.append(f"--registry-mirror={REGISTRY}")
        if REGISTRY_SCHEME == "http":
            args.append("--insecure-pull")

    # kaniko build can be launched without privilege but
    # it needs some capabilities and to be root
    # https://github.com/GoogleContainerTools/kaniko/issues/778
    capabilities = ["CHOWN", "SETUID", "SETGID", "FOWNER", "DAC_OVERRIDE"]
    container_security_context = get_security_context(root=True, capabilities=capabilities)

    container = kubernetes.client.V1Container(
        name=pod_name,
        image=image,
        command=command,
        args=args,
        volume_mounts=[
            {
                "name": "dockerfile",
                "mountPath": mount_path_dockerfile,
                "subPath": dockerfile_mount_subpath,
                "readOnly": True,
            }
        ],
        security_context=container_security_context,
    )

    container.volume_mounts.append(
        {
            "name": "cache",
            "mountPath": "/cache",
            "readOnly": True,
        }
    )

    if KANIKO_DOCKER_CONFIG_SECRET_NAME:
        container.volume_mounts.append({"name": "docker-config", "mountPath": "/kaniko/.docker"})

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
        containers=[container],
        volumes=[
            {
                "name": "dockerfile",
                "persistentVolumeClaim": {
                    "claimName": settings.WORKER_PVC_SUBTUPLE
                    if settings.WORKER_PVC_IS_HOSTPATH
                    else get_worker_subtuple_pvc_name()
                },
            }
        ],
    )

    spec.volumes.append(
        {
            "name": "cache",
            "persistentVolumeClaim": {
                "claimName": settings.WORKER_PVC_DOCKER_CACHE
                if settings.WORKER_PVC_IS_HOSTPATH
                else get_docker_cache_pvc_name()
            },
        }
    )

    if KANIKO_DOCKER_CONFIG_SECRET_NAME:
        spec.volumes.append(
            {
                "name": "docker-config",
                "secret": {
                    "secretName": KANIKO_DOCKER_CONFIG_SECRET_NAME,
                    "items": [{"key": ".dockerconfigjson", "path": "config.json"}],
                },
            }
        )

    pod = kubernetes.client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=kubernetes.client.V1ObjectMeta(
            name=pod_name,
            labels={
                Label.PodName: pod_name,
                Label.PodType: "image-build",
                Label.Component: Label.Component_Compute,
            },
        ),
        spec=spec,
    )

    create_pod = not pod_exists(k8s_client, pod_name)
    if create_pod:
        try:
            logger.info("creating pod: building image", namespace=NAMESPACE, pod=pod_name, image=tag)
            k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)
        except kubernetes.client.rest.ApiException as e:
            raise Exception(
                f"Error creating pod {NAMESPACE}/{pod_name}. Reason: {e.reason}, status: {e.status}, body: {e.body}"
            ) from None

    try:
        watch_pod(k8s_client, pod_name)
    except Exception as e:
        # In case of concurrent build, it may fail
        # check if image exists
        if not container_image_exists(tag):
            raise compute_task_errors.BuildError from e
    finally:
        if create_pod:
            log_prefix = f"[{ctx.compute_plan_key[:8]}-{ctx.task_key[:8]}-b-{ctx.attempt}]"
            _container_format_log(pod_name, get_pod_logs(k8s_client, name=pod_name, container=pod_name), log_prefix)
            delete_pod(k8s_client, pod_name)


def _assert_dockerfile(dockerfile_path):
    dockerfile_fullpath = os.path.join(dockerfile_path, "Dockerfile")
    if not os.path.exists(dockerfile_fullpath):
        raise Exception(f"Dockerfile does not exist : {dockerfile_fullpath}")


def _container_format_log(container_name, container_logs, log_prefix):
    if isinstance(container_logs, bytes):
        logs = [f"{log_prefix} {log}" for log in container_logs.decode().split("\n")]
    else:
        logs = [f"{log_prefix} {log}" for log in container_logs.split("\n")]

    for log in logs:
        logger.info(log)
