import kubernetes
import requests
import os
import logging
from django.conf import settings
from substrapp.utils import timeit
from substrapp.exceptions import PodErrorException, PodTimeoutException
import time

logger = logging.getLogger(__name__)


MEDIA_ROOT = os.getenv('MEDIA_ROOT')
REGISTRY = os.getenv('REGISTRY')
REGISTRY_SCHEME = os.getenv('REGISTRY_SCHEME')
REGISTRY_PULL_DOMAIN = os.getenv('REGISTRY_PULL_DOMAIN')
NAMESPACE = os.getenv('NAMESPACE')
NODE_NAME = os.getenv('NODE_NAME')
COMPONENT = 'substra-compute'
RUN_AS_GROUP = os.getenv('RUN_AS_GROUP')
RUN_AS_USER = os.getenv('RUN_AS_USER')
FS_GROUP = os.getenv('FS_GROUP')
KANIKO_MIRROR = settings.TASK['KANIKO_MIRROR']
KANIKO_IMAGE = settings.TASK['KANIKO_IMAGE']
COMPUTE_REGISTRY = settings.TASK['COMPUTE_REGISTRY']
HTTP_CLIENT_TIMEOUT_SECONDS = getattr(settings, 'HTTP_CLIENT_TIMEOUT_SECONDS')
REGISTRY_IS_LOCAL = settings.REGISTRY_IS_LOCAL
REGISTRY_SERVICE_NAME = settings.REGISTRY_SERVICE_NAME

K8S_PVC = {
    env_key: env_value for env_key, env_value in os.environ.items() if '_PVC' in env_key
}


class ImageNotFound(Exception):
    pass


class BuildError(Exception):
    pass


def k8s_get_cache_index_lock_file(cache_index):
    return f'/tmp/cache-index-{cache_index}.lock'


def k8s_try_create_file(path):
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL)
        os.close(fd)
        return True
    except FileExistsError:
        return False


def k8s_acquire_cache_index():
    celery_worker_concurrency = int(getattr(settings, 'CELERY_WORKER_CONCURRENCY'))

    if celery_worker_concurrency == 1:
        return None

    max_attempts = 12
    attempt = 0

    while attempt < max_attempts:
        for cache_index in range(1, celery_worker_concurrency + 1):
            lock_file = k8s_get_cache_index_lock_file(cache_index)
            if k8s_try_create_file(lock_file):
                return str(cache_index)
            attempt += 1

    raise Exception(f'Could not acquire cache index after {max_attempts} attempts')


def k8s_release_cache_index(cache_index):
    if cache_index is None:
        return
    lock_file = k8s_get_cache_index_lock_file(cache_index)
    try:
        os.remove(lock_file)
    except FileNotFoundError:
        pass


def watch_pod(name, watch_init_container=False):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    finished = False
    attempt = 0
    max_attempts = 5 + (5 if watch_init_container else 0)
    error = None
    watch_container = not watch_init_container

    logger.info(f'Waiting for pod {name}...')

    pod_status = None

    while (not finished) and (attempt < max_attempts):
        try:
            api_response = k8s_client.read_namespaced_pod_status(
                name=name,
                namespace=NAMESPACE,
                pretty=True
            )

            if api_response.status.phase != pod_status:
                pod_status = api_response.status.phase
                logger.info(f'Status for pod "{name}" {api_response.status.phase} status')

            # Handle pod error not linked with containers
            if api_response.status.phase == 'Failed' or (api_response.status.reason and
               'Evicted' in api_response.status.reason):

                if api_response.status.reason:
                    error = api_response.status.reason
                else:
                    error = f'Pod phase : {api_response.status.phase}'

                logger.error(f'Status for pod "{name}" {api_response.status.phase.lower()} status')
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
                                error = 'InitContainer: ' + get_pod_error(state.terminated)
                            else:
                                watch_container = True  # Init container is ready
                        else:
                            if state.waiting and state.waiting.reason not in ['PodInitializing', 'ContainerCreating']:
                                error = 'InitContainer: ' + get_pod_error(state.waiting)
                                attempt += 1
                                logger.error(f'InitContainer for pod "{name}" waiting status '
                                             f'(attempt {attempt}/{max_attempts}): {state.waiting.message}')

            if watch_container:
                if api_response.status.container_statuses:
                    for container in api_response.status.container_statuses:
                        state = container.state
                        if state.terminated:
                            finished = True
                            error = None
                            if state.terminated.exit_code != 0:
                                error = get_pod_error(state.terminated)

                        else:
                            # {"ContainerCreating", "CrashLoopBackOff", "CreateContainerConfigError",
                            #  "ErrImagePull", "ImagePullBackOff", "CreateContainerError", "InvalidImageName"}
                            if state.waiting and state.waiting.reason not in ['PodInitializing', 'ContainerCreating']:
                                error = get_pod_error(state.waiting)
                                attempt += 1
                                logger.error(f'Container for pod "{name}" waiting status '
                                             f'(attempt {attempt}/{max_attempts}): {state.waiting.message}')

            if not finished:
                time.sleep(0.2)

        except Exception as e:
            attempt += 1
            logger.error(f'Could not get pod "{name}" status (attempt {attempt}/{max_attempts}): {e}')

    if error is not None:
        raise PodErrorException(f'Pod {name} terminated with error: {error}')

    if not finished:
        raise PodTimeoutException(f'Pod {name} didn\'t complete after {max_attempts} attempts')


def get_pod_error(state):
    error = state.reason
    if state.message is not None:
        error += f' ({state.message})'
    return error


def get_pod_name(name):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.list_namespaced_pod(
        NAMESPACE,
        label_selector=f'app={name}'
    )
    if api_response.items:
        pod = api_response.items.pop()
    else:
        raise Exception(f'Could not get pod name {name}')

    return pod.metadata.name


def pod_exists(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    try:
        k8s_client.read_namespaced_pod(
            name=name,
            namespace=NAMESPACE)
    except Exception:
        return False
    else:
        return True


def wait_for_pod_deletion(name):
    while pod_exists(name):
        pass


@timeit
def get_pod_logs(name, container):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    logs = f'No logs for pod {name}'

    if pod_exists(name):
        try:
            logs = k8s_client.read_namespaced_pod_log(
                name=name,
                namespace=NAMESPACE,
                container=container
            )
        except Exception:
            pass

    return logs


def container_format_log(container_name, container_logs):

    if isinstance(container_logs, bytes):
        logs = [f'[{container_name}] {log}' for log in container_logs.decode().split('\n')]
    else:
        logs = [f'[{container_name}] {log}' for log in container_logs.split('\n')]

    for log in logs:
        logger.info(log)


@timeit
def k8s_build_image(path, tag, rm):
    try:
        cache_index = k8s_acquire_cache_index()
        _k8s_build_image(path, tag, rm, cache_index)
    except Exception:
        raise
    finally:
        k8s_release_cache_index(cache_index)


def _k8s_build_image(path, tag, rm, cache_index):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    job_name = f'kaniko-{tag.split("/")[-1].replace("_", "-")}'

    dockerfile_fullpath = os.path.join(path, 'Dockerfile')

    dockerfile_mount_subpath = path.split('/subtuple/')[-1]

    # kaniko build can be launched without privilege but
    # it needs some capabilities and to be root
    image = KANIKO_IMAGE
    command = None
    mount_path_dockerfile = path
    mount_path_cache = '/cache'

    args = [
        f'--dockerfile={dockerfile_fullpath}',
        f'--context=dir://{path}',
        f'--destination={REGISTRY}/{tag}:substra',
        f'--cache={str(not(rm)).lower()}',
        '--snapshotMode=redo',
        '--single-snapshot'
    ]

    if REGISTRY_SCHEME == 'http':
        args.append('--insecure')

    if KANIKO_MIRROR:
        args.append(f'--registry-mirror={REGISTRY}')
        if REGISTRY_SCHEME == 'http':
            args.append('--insecure-pull')

    # https://github.com/GoogleContainerTools/kaniko/issues/778
    capabilities = ['CHOWN', 'SETUID', 'SETGID', 'FOWNER', 'DAC_OVERRIDE']
    pod_security_context = get_pod_security_context(root=True)
    container_security_context = get_security_context(root=True, add_capabilities=capabilities)

    container = kubernetes.client.V1Container(
        name=job_name,
        image=image if not COMPUTE_REGISTRY else f'{COMPUTE_REGISTRY}/{image}',
        command=command,
        args=args,
        volume_mounts=[
            {'name': 'dockerfile',
             'mountPath': mount_path_dockerfile,
             'subPath': dockerfile_mount_subpath,
             'readOnly': True}
        ],
        security_context=container_security_context
    )

    if mount_path_cache is not None:
        container.volume_mounts.append({
            'name': 'cache',
            'mountPath': mount_path_cache,
            'subPath': cache_index,
            'readOnly': True
        })

    pod_affinity = kubernetes.client.V1Affinity(
        pod_affinity=kubernetes.client.V1PodAffinity(
            required_during_scheduling_ignored_during_execution=[
                kubernetes.client.V1PodAffinityTerm(
                    label_selector=kubernetes.client.V1LabelSelector(
                        match_expressions=[
                            kubernetes.client.V1LabelSelectorRequirement(
                                key="app.kubernetes.io/component",
                                operator="In",
                                values=["substra-worker"]
                            )
                        ]
                    ),
                    topology_key="kubernetes.io/hostname"
                )
            ]
        )
    )

    spec = kubernetes.client.V1PodSpec(
        restart_policy='Never',
        affinity=pod_affinity,
        containers=[container],
        volumes=[
            {
                'name': 'dockerfile',
                'persistentVolumeClaim': {'claimName': K8S_PVC['SUBTUPLE_PVC']}
            }
        ],
        security_context=pod_security_context
    )

    if mount_path_cache is not None:
        spec.volumes.append({
            'name': 'cache',
            'persistentVolumeClaim': {'claimName': K8S_PVC['DOCKER_CACHE_PVC']}
        })

    pod = kubernetes.client.V1Pod(
        api_version='v1',
        kind='Pod',
        metadata=kubernetes.client.V1ObjectMeta(
            name=job_name,
            labels={'app': job_name, 'task': 'build',
                    'app.kubernetes.io/component': COMPONENT}
        ),
        spec=spec
    )

    create_pod = not pod_exists(job_name)
    if create_pod:
        try:
            logger.info(f'Creating pod {NAMESPACE}/{job_name}')
            k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)
        except kubernetes.client.rest.ApiException as e:
            raise Exception(f'Error creating pod {NAMESPACE}/{job_name}. Reason: {e.reason}, status: {e.status}, '
                            f'body: {e.body}') from None

    try:
        watch_pod(job_name)
    except Exception as e:
        # In case of concurrent build, it may fail
        # check if image exists
        if not k8s_image_exists(tag):
            logger.error(f'Kaniko build failed, error: {e}')
            raise BuildError(f'Kaniko build failed, error: {e}')
    finally:
        if create_pod:
            container_format_log(
                job_name,
                get_pod_logs(name=get_pod_name(job_name),
                             container=job_name)
            )
            k8s_client.delete_namespaced_pod(
                name=job_name,
                namespace=NAMESPACE,
                body=kubernetes.client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=0
                )
            )


@timeit
def k8s_get_image(image_name):
    response = requests.get(
        f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/substra',
        headers={'Accept': 'application/json'},
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    return response.json()


def k8s_image_exists(image_name):
    try:
        k8s_get_image(image_name)
    except ImageNotFound:
        return False
    else:
        return True


def k8s_remove_image(image_name):
    logger.info(f'Deleting image {image_name}')
    try:
        response = requests.get(
            f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/substra',
            headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS
        )

        if response.status_code != requests.status_codes.codes.ok:
            # raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')
            return

        digest = response.headers['Docker-Content-Digest']

        response = requests.delete(
            f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/{digest}',
            headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'},
            timeout=HTTP_CLIENT_TIMEOUT_SECONDS
        )
        if response.status_code != requests.status_codes.codes.accepted:
            # raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')
            return
    except Exception as e:
        logger.exception(e)


@timeit
def k8s_compute(image_name, job_name, command, volumes, task_label,
                capture_logs, environment, remove_image, subtuple_key, compute_plan_key):

    pull_domain = REGISTRY_PULL_DOMAIN

    if REGISTRY_IS_LOCAL:
        try:
            registry_port = get_docker_registry_port()
        except Exception as e:
            raise Exception("Failed to retrieve docker registry node port") from e
        pull_domain += f":{registry_port}"

    # We cannot currently set up shm_size
    # Suggestion  https://github.com/timescale/timescaledb-kubernetes/pull/131/files
    # 'shm_size': '8G'

    task_args = {
        'image': f'{pull_domain}/{image_name}:substra',
        'name': job_name,
        'command': command,
        'volumes': volumes,
        'label': task_label,
        'environment': environment
    }

    try:
        _k8s_compute(job_name, task_args, subtuple_key)
    except (PodErrorException, PodTimeoutException) as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.exception(e)
        raise
    finally:

        if capture_logs:
            container_format_log(
                job_name,
                get_pod_logs(name=get_pod_name(job_name),
                             container=job_name)
            )

        delete_compute_pod(job_name)

        # Remove images
        if remove_image:
            k8s_remove_image(image_name)


def generate_volumes(volume_binds, name, subtuple_key):
    volume_mounts = []
    volumes = []

    for path, bind in volume_binds.items():

        if '/servermedias/' in path:
            # /MOUNT/PATH/servermedias/...
            volume_name = 'servermedias'
        else:
            # /MOUNT/PATH/medias/volume_name/...
            volume_name = path.split('/medias/')[-1].split('/')[0]

        subpath = path.split(f'/{volume_name}/')[-1]

        pvc_name = [key for key in K8S_PVC.keys()
                    if volume_name in key.lower()]
        if pvc_name:
            pvc_name = pvc_name.pop()
        else:
            raise Exception(f'PVC for {volume_name} not found')

        volume_mounts.append({
            'name': volume_name,
            'mountPath': bind['bind'],
            'subPath': subpath,
            'readOnly': bind['mode'] != 'rw'

        })

        volumes.append({
            'name': volume_name,
            'persistentVolumeClaim': {'claimName': K8S_PVC[pvc_name]}
        })

    # Unique volumes
    volumes = list({v['name']: v for v in volumes}.values())

    return volume_mounts, volumes


@timeit
def _k8s_compute(name, task_args, subtuple_key):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    volume_mounts, volumes = generate_volumes(task_args['volumes'], name, subtuple_key)

    container_compute = kubernetes.client.V1Container(
        name=name,
        image=task_args['image'],
        args=task_args['command'].split(" ") if task_args['command'] is not None else None,
        volume_mounts=volume_mounts,
        # resources=get_resources(task_args),
        security_context=get_security_context(),
        env=[kubernetes.client.V1EnvVar(name=env_name, value=env_value)
             for env_name, env_value in task_args['environment'].items()]
    )

    pod_affinity = kubernetes.client.V1Affinity(
        pod_affinity=kubernetes.client.V1PodAffinity(
            required_during_scheduling_ignored_during_execution=[
                kubernetes.client.V1PodAffinityTerm(
                    label_selector=kubernetes.client.V1LabelSelector(
                        match_expressions=[
                            kubernetes.client.V1LabelSelectorRequirement(
                                key="app.kubernetes.io/component",
                                operator="In",
                                values=["substra-worker"]
                            )
                        ]
                    ),
                    topology_key="kubernetes.io/hostname"
                )
            ]
        )
    )

    spec = kubernetes.client.V1PodSpec(
        restart_policy='Never',
        affinity=pod_affinity,
        containers=[container_compute],
        volumes=volumes,
        security_context=get_pod_security_context()
    )

    pod = kubernetes.client.V1Pod(
        api_version='v1',
        kind='Pod',
        metadata=kubernetes.client.V1ObjectMeta(name=name,
                                                labels={'app': name,
                                                        'task': task_args['label'],
                                                        'app.kubernetes.io/component': COMPONENT}
                                                ),
        spec=spec
    )

    try:
        logger.info(f'Creating pod {NAMESPACE}/{name}')
        k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)
    except kubernetes.client.rest.ApiException as e:
        raise Exception(f'Error creating pod {NAMESPACE}/{name}. Reason: {e.reason}, status: {e.status}, '
                        f'body: {e.body}') from None

    watch_pod(name)


@timeit
def delete_compute_pod(name):

    if pod_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.CoreV1Api()

        k8s_client.delete_namespaced_pod(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=0
            )
        )

    wait_for_pod_deletion(name)
    logger.info(f'Deleted pod {NAMESPACE}/{name}')


def get_security_context(enabled=True, root=False, privileged=False, add_capabilities=None):
    if enabled:
        if not root:
            return kubernetes.client.V1SecurityContext(
                privileged=privileged,
                allow_privilege_escalation=privileged,
                capabilities=kubernetes.client.V1Capabilities(drop=['ALL'],
                                                              add=add_capabilities),
                run_as_non_root=True,
                run_as_group=int(RUN_AS_GROUP),
                run_as_user=int(RUN_AS_USER)
            )
        else:
            return kubernetes.client.V1SecurityContext(
                privileged=privileged,
                allow_privilege_escalation=privileged,
                capabilities=kubernetes.client.V1Capabilities(drop=['ALL'],
                                                              add=add_capabilities),
            )

    return None


def get_pod_security_context(enabled=True, root=False):
    if enabled:
        if not root:
            return kubernetes.client.V1PodSecurityContext(
                run_as_non_root=True,
                fs_group=int(FS_GROUP),
                run_as_group=int(RUN_AS_GROUP),
                run_as_user=int(RUN_AS_USER)
            )

    return None


def get_docker_registry_port() -> int:
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    svc = k8s_client.read_namespaced_service(REGISTRY_SERVICE_NAME, NAMESPACE)

    return svc.spec.ports[0].node_port
