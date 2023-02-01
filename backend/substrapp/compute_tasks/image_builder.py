import json
import os
from tempfile import TemporaryDirectory

import kubernetes
import structlog
from django.conf import settings

import orchestrator
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks import utils
from substrapp.compute_tasks.compute_pod import Label
from substrapp.compute_tasks.datastore import Datastore
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
KANIKO_DOCKER_CONFIG_VOLUME_NAME = "docker-config"
CELERY_WORKER_CONCURRENCY = settings.CELERY_WORKER_CONCURRENCY
SUBTUPLE_TMP_DIR = settings.SUBTUPLE_TMP_DIR
MAX_IMAGE_BUILD_TIME = 3 * 60 * 60  # 3 hours
KANIKO_CONTAINER_NAME = "kaniko"
HOSTNAME = settings.HOSTNAME


def build_image_if_missing(datastore: Datastore, function: orchestrator.Function) -> None:
    """
    Build the container image and the ImageEntryPoint entry if they don't exist already
    """
    container_image_tag = utils.container_image_tag_from_function(function)
    with lock_resource("image-build", container_image_tag, ttl=MAX_IMAGE_BUILD_TIME, timeout=MAX_IMAGE_BUILD_TIME):
        if container_image_exists(container_image_tag):
            logger.info("Reusing existing image", image=container_image_tag)
        else:
            asset_content = datastore.get_function(function)
            _build_function_image(asset_content, function)


def _build_function_image(asset: bytes, function: orchestrator.Function) -> None:
    """
    Build an function's container image.

    Perform multiple steps:
    1. Download the function using the provided asset storage_address/owner. Verify its checksum and uncompress the data
       to a temporary folder.
    2. Extract the ENTRYPOINT from the Dockerfile.
    3. Build the container image using Kaniko.
    4. Save the ENTRYPOINT to the DB
    """

    os.makedirs(SUBTUPLE_TMP_DIR, exist_ok=True)

    with TemporaryDirectory(dir=SUBTUPLE_TMP_DIR) as tmp_dir:
        # Download source
        uncompress_content(asset, tmp_dir)

        # Extract ENTRYPOINT from Dockerfile
        entrypoint = _get_entrypoint_from_dockerfile(tmp_dir)

        # Build image
        _build_container_image(tmp_dir, utils.container_image_tag_from_function(function))

        # Save entrypoint to DB if the image build was successful
        ImageEntrypoint.objects.get_or_create(function_checksum=function.function.checksum, entrypoint_json=entrypoint)


def _get_entrypoint_from_dockerfile(dockerfile_dir: str) -> list[str]:
    """
    Get entrypoint from ENTRYPOINT in the Dockerfile.

    This is necessary because the user function can have arbitrary names, ie; "myfunction.py".

    Example:
        ENTRYPOINT ["python3", "myfunction.py"]
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
                        "Invalid ENTRYPOINT in function/metric Dockerfile. "
                        "You must use the exec form in your Dockerfile. "
                        "See https://docs.docker.com/engine/reference/builder/#entrypoint"
                    )
                return res

    raise compute_task_errors.BuildError("Invalid Dockerfile: Cannot find ENTRYPOINT")


@timeit
def _build_container_image(path: str, tag: str) -> None:
    _assert_dockerfile_exist(path)

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    pod_name = _build_pod_name(tag)

    create_pod = not pod_exists(k8s_client, pod_name)
    if create_pod:
        try:
            logger.info("creating pod: building image", namespace=NAMESPACE, pod=pod_name, image=tag)
            pod = _build_pod(path, tag)
            k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)
        except kubernetes.client.ApiException as e:
            raise compute_task_errors.BuildError(
                f"Error creating pod {NAMESPACE}/{pod_name}. Reason: {e.reason}, status: {e.status}, body: {e.body}"
            ) from e

    build_exc = None

    try:
        watch_pod(k8s_client, pod_name)

    except Exception as e:
        # In case of concurrent builds, it may fail. Check if the image exists.
        if container_image_exists(tag):
            return
        build_exc = e

    finally:
        logs = None

        if create_pod:
            logs = get_pod_logs(k8s_client, pod_name, KANIKO_CONTAINER_NAME, ignore_pod_not_found=True)
            delete_pod(k8s_client, pod_name)
            for line in (logs or "").split("\n"):
                logger.info(line, pod_name=pod_name)

        if build_exc:
            err_msg = str(build_exc)
            if logs:
                err_msg += "\n\n" + logs
            raise compute_task_errors.BuildError(err_msg)


def _assert_dockerfile_exist(dockerfile_path):
    dockerfile_fullpath = os.path.join(dockerfile_path, "Dockerfile")
    if not os.path.exists(dockerfile_fullpath):
        raise compute_task_errors.BuildError(f"Dockerfile does not exist : {dockerfile_fullpath}")


def _build_pod(dockerfile_mount_path: str, image_tag: str) -> kubernetes.client.V1Pod:
    pod_name = _build_pod_name(image_tag)
    pod_spec = _build_pod_spec(dockerfile_mount_path, image_tag)
    return kubernetes.client.V1Pod(
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
        spec=pod_spec,
    )


def _build_pod_name(image_tag: str) -> str:
    dns_1123_compliant_tag = image_tag.split("/")[-1].replace("_", "-")
    return f"kaniko-{dns_1123_compliant_tag}"


def _build_pod_spec(dockerfile_mount_path: str, image_tag: str) -> kubernetes.client.V1PodSpec:
    container = _build_container(dockerfile_mount_path, image_tag)
    pod_affinity = _build_pod_affinity()

    cache_pvc_name = (
        settings.WORKER_PVC_DOCKER_CACHE if settings.WORKER_PVC_IS_HOSTPATH else get_docker_cache_pvc_name()
    )
    cache = kubernetes.client.V1Volume(
        name="cache",
        persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(claim_name=cache_pvc_name),
    )

    dockerfile_pvc_name = (
        settings.WORKER_PVC_SUBTUPLE if settings.WORKER_PVC_IS_HOSTPATH else get_worker_subtuple_pvc_name()
    )
    dockerfile = kubernetes.client.V1Volume(
        name="dockerfile",
        persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(claim_name=dockerfile_pvc_name),
    )

    volumes = [cache, dockerfile]

    if KANIKO_DOCKER_CONFIG_SECRET_NAME:
        docker_config = kubernetes.client.V1Volume(
            name=KANIKO_DOCKER_CONFIG_VOLUME_NAME,
            secret=kubernetes.client.V1SecretVolumeSource(
                secret_name=KANIKO_DOCKER_CONFIG_SECRET_NAME,
                items=[kubernetes.client.V1KeyToPath(key=".dockerconfigjson", path="config.json")],
            ),
        )
        volumes.append(docker_config)

    return kubernetes.client.V1PodSpec(
        restart_policy="Never", affinity=pod_affinity, containers=[container], volumes=volumes
    )


def _build_pod_affinity() -> kubernetes.client.V1Affinity:
    return kubernetes.client.V1Affinity(
        pod_affinity=kubernetes.client.V1PodAffinity(
            required_during_scheduling_ignored_during_execution=[
                kubernetes.client.V1PodAffinityTerm(
                    label_selector=kubernetes.client.V1LabelSelector(
                        match_expressions=[
                            kubernetes.client.V1LabelSelectorRequirement(
                                key="statefulset.kubernetes.io/pod-name", operator="In", values=[HOSTNAME]
                            )
                        ]
                    ),
                    topology_key="kubernetes.io/hostname",
                )
            ]
        )
    )


def _build_container(dockerfile_mount_path: str, image_tag: str) -> kubernetes.client.V1Container:
    # kaniko build can be launched without privilege but
    # it needs some capabilities and to be root
    # https://github.com/GoogleContainerTools/kaniko/issues/778
    # https://github.com/GoogleContainerTools/kaniko/issues/778#issuecomment-619112417
    # https://github.com/moby/moby/blob/master/oci/caps/defaults.go
    # https://man7.org/linux/man-pages/man7/capabilities.7.html
    capabilities = ["CHOWN", "SETUID", "SETGID", "FOWNER", "DAC_OVERRIDE", "SETFCAP"]
    container_security_context = get_security_context(root=True, capabilities=capabilities)
    args = _build_container_args(dockerfile_mount_path, image_tag)
    dockerfile_mount_subpath = dockerfile_mount_path.split("/subtuple/")[-1]

    dockerfile = kubernetes.client.V1VolumeMount(
        name="dockerfile", mount_path=dockerfile_mount_path, sub_path=dockerfile_mount_subpath, read_only=True
    )
    cache = kubernetes.client.V1VolumeMount(name="cache", mount_path="/cache", read_only=True)
    volume_mounts = [dockerfile, cache]

    if KANIKO_DOCKER_CONFIG_SECRET_NAME:
        docker_config = kubernetes.client.V1VolumeMount(
            name=KANIKO_DOCKER_CONFIG_VOLUME_NAME, mount_path="/kaniko/.docker"
        )
        volume_mounts.append(docker_config)

    return kubernetes.client.V1Container(
        name=KANIKO_CONTAINER_NAME,
        image=KANIKO_IMAGE,
        command=None,
        args=args,
        volume_mounts=volume_mounts,
        security_context=container_security_context,
    )


def _build_container_args(dockerfile_mount_path: str, image_tag: str) -> list[str]:
    dockerfile_fullpath = os.path.join(dockerfile_mount_path, "Dockerfile")
    args = [
        f"--dockerfile={dockerfile_fullpath}",
        f"--context=dir://{dockerfile_mount_path}",
        f"--destination={REGISTRY}/{USER_IMAGE_REPOSITORY}:{image_tag}",
        "--cache=true",
        "--log-timestamp=true",
        "--snapshotMode=redo",
        "--push-retry=3",
        "--cache-copy-layers",
        "--log-format=text",
        f"--verbosity={('debug' if settings.LOG_LEVEL == 'DEBUG' else 'info')}",
    ]

    if REGISTRY_SCHEME == "http":
        args.append("--insecure")

    if KANIKO_MIRROR:
        args.append(f"--registry-mirror={REGISTRY}")
        if REGISTRY_SCHEME == "http":
            args.append("--insecure-pull")
    return args
