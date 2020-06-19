import math
import json
import kubernetes
import requests
import os
import logging

from substrapp.utils import timeit, to_bool

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
SC_ON_CLEAN = to_bool(os.getenv('SC_ON_CLEAN'))
IMAGE_BUILDER = os.getenv('IMAGE_BUILDER')

K8S_PVC = {
    env_key: env_value for env_key, env_value in os.environ.items() if '_PVC' in env_key
}


class ImageNotFound(Exception):
    pass


class BuildError(Exception):
    pass


def k8s_memory_limit(celery_worker_concurrency, celeryworker_image):
    # celeryworker_image useless but for compatiblity
    # Get memory limit from node through the API

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    node = k8s_client.read_node(NODE_NAME)

    return (int(node.status.allocatable['memory'][:-2]) / 1024) // celery_worker_concurrency


def k8s_cpu_count(celeryworker_image):
    # celeryworker_image useless but for compatiblity
    # Get CPU count from node through the API

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    node = k8s_client.read_node(NODE_NAME)

    cpu_allocatable = node.status.allocatable['cpu']

    # convert XXXXm cpu to X.XXX cpu
    if 'm' in cpu_allocatable:
        cpu_allocatable = float(cpu_allocatable.replace('m', '')) / 1000.0

    return max(1, math.floor(float(cpu_allocatable)))


def k8s_gpu_list(celeryworker_image):

    # if you don't request GPUs when using the device plugin with
    # NVIDIA images all the GPUs on the machine will be exposed inside your container.

    import GPUtil
    import json

    return json.dumps([str(gpu.id) for gpu in GPUtil.getGPUs()])


def k8s_cpu_used(task_label):
    # Get CPU used from node through the API

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.list_namespaced_pod(
        NAMESPACE,
        label_selector=f'task={task_label}'
    )

    cpu_used = 0

    for pod in api_response.items:
        for container in pod.spec.containers:
            if container.resources.limits is not None:
                cpu_used += int(getattr(container.resources.limits, 'cpu', 0))

    if cpu_used:
        return [f'0-{cpu_used}']
    else:
        return []


def k8s_gpu_used(task_label):
    # Get GPU used from k8s through the API
    # Because the execution may be remote

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.list_namespaced_pod(
        NAMESPACE,
        label_selector=f'task={task_label}'
    )

    gpu_used = 0

    for pod in api_response.items:
        for container in pod.spec.containers:
            if container.resources.limits is not None:
                gpu_used += int(getattr(container.resources.limits, 'nvidia.com/gpu', 0))

    return [','.join(range(gpu_used))]


def watch_pod(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    finished = False
    attempt = 0
    max_attempts = 5
    error = None

    while (not finished) and (attempt < max_attempts):
        try:
            api_response = k8s_client.read_namespaced_pod_status(
                name=name,
                namespace=NAMESPACE,
                pretty=True
            )

            if api_response.status.container_statuses:
                for container in api_response.status.container_statuses:
                    if container.state.terminated:
                        finished = True
                        error = None
                        if container.state.terminated.exit_code != 0:
                            error = container.state.terminated.reason

                    else:
                        # {"ContainerCreating", "CrashLoopBackOff", "CreateContainerConfigError",
                        #  "ErrImagePull", "ImagePullBackOff", "CreateContainerError", "InvalidImageName"}
                        if container.state.waiting and container.state.waiting.reason not in ['ContainerCreating']:
                            error = container.state.waiting.reason
                            attempt += 1
                            logger.error(f'Container for pod "{name}" waiting status '
                                         f'(attempt {attempt}/{max_attempts}): {container.state.waiting.message}')
                            time.sleep(0.5)

        except Exception as e:
            attempt += 1
            logger.error(f'Could not get pod "{name}" status (attempt {attempt}/{max_attempts}): {e}')

    if not finished or error is not None:
        raise Exception(f'Pod {name} could not have a completed state '
                        f'after {attempt}/{max_attempts} attempts : {error}')


def get_pod_name(name):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.list_namespaced_pod(
        NAMESPACE,
        label_selector=f'app={name}'
    )
    if api_response.items:
        pod = api_response.items.pop()

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


def k8s_build_image(path, tag, rm):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    job_name = f'{IMAGE_BUILDER}-{tag.split("/")[-1].replace("_", "-")}'

    logger.info(f'The pod {NAMESPACE}/{job_name} started')

    dockerfile_fullpath = os.path.join(path, 'Dockerfile')

    dockerfile_mount_subpath = path.split('/subtuple/')[-1]

    if IMAGE_BUILDER == 'kaniko':
        image = 'gcr.io/kaniko-project/executor:v0.23.0'
        command = None
        mount_path_cache = '/cache'
        args = [
            f'--dockerfile={dockerfile_fullpath}',
            f'--context=dir://{path}',
            f'--destination={REGISTRY}/{tag}:substra',
            f'--cache={str(not(rm)).lower()}'
        ]

        if REGISTRY_SCHEME == 'http':
            args.append('--insecure')

        pod_security_context = None
        container_security_context = None

    elif IMAGE_BUILDER == 'makisu':
        image = 'gcr.io/uber-container-tools/makisu:v0.2.0'
        command = None
        mount_path_cache = '/tmp'
        args = [
            'build',
            f'--push={REGISTRY}',
            f'-t={tag}:substra',
        ]

        if REGISTRY_SCHEME == 'http':
            registry_config = json.dumps(
                {"*": {"*": {"security": {"tls": {"client": {"disabled": True}}}}}}
            )
            args.extend(['--registry-config', registry_config])

        args.append(path)

        pod_security_context = get_pod_security_context()
        container_security_context = get_security_context()

    elif IMAGE_BUILDER == 'dind':
        image = 'docker:19.03-dind'
        command = ['/bin/sh', '-c']
        mount_path_cache = '/var/lib/docker'
        wait_for_docker = 'while ! (docker ps); do sleep 1; done'
        build_args = (
            f'docker build -t "{REGISTRY}/{tag}:substra" {path} ;'
            f'docker push {REGISTRY}/{tag}:substra')

        if REGISTRY_SCHEME == 'http':
            extra_options = f'--insecure-registry={REGISTRY}'
        else:
            extra_options = ''
        args = [f'(dockerd-entrypoint.sh {extra_options}) & {wait_for_docker}; {build_args}']

        pod_security_context = None
        container_security_context = kubernetes.client.V1SecurityContext(
            privileged=True
        )

    container = kubernetes.client.V1Container(
        name=job_name,
        image=image,
        command=command,
        args=args,
        volume_mounts=[
            {'name': 'dockerfile',
             'mountPath': path,
             'subPath': dockerfile_mount_subpath,
             'readOnly': True},

            {'name': 'cache',
             'mountPath': mount_path_cache,
             'readOnly': (IMAGE_BUILDER == 'kaniko')}
        ],
        security_context=container_security_context
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
        containers=[container],
        volumes=[
            {
                'name': 'dockerfile',
                'persistentVolumeClaim': {'claimName': K8S_PVC['SUBTUPLE_PVC']}
            },
            {
                'name': 'cache',
                'persistentVolumeClaim': {'claimName': K8S_PVC['DOCKER_CACHE_PVC']}
            }
        ],
        security_context=pod_security_context
    )

    pod = kubernetes.client.V1Pod(
        api_version='v1',
        kind='Pod',
        metadata=kubernetes.client.V1ObjectMeta(
            name=job_name,
            labels={'app': job_name, 'app.kubernetes.io/component': COMPONENT}
        ),
        spec=spec
    )

    k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)

    try:
        watch_pod(job_name)
    except Exception as e:
        logger.error(f'{IMAGE_BUILDER} build failed, error: {e}')
        raise BuildError(f'{IMAGE_BUILDER} build failed, error: {e}')
    finally:
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


def k8s_get_image(image_name):
    response = requests.get(
        f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/substra',
        headers={'Accept': 'application/json'}
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    return response.json()


def k8s_remove_image(image_name):

    try:
        response = requests.get(
            f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/substra',
            headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        )

        if response.status_code != requests.status_codes.codes.ok:
            # raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')
            return

        digest = response.headers['Docker-Content-Digest']

        response = requests.delete(
            f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/{digest}',
            headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        )
        if response.status_code != requests.status_codes.codes.accepted:
            # raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')
            return
    except Exception as e:
        logger.exception(e)


@timeit
def k8s_compute(image_name, job_name, cpu_set, memory_limit_mb, command, volumes, task_label,
                capture_logs, environment, gpu_set, remove_image, subtuple_key, compute_plan_id):

    # We cannot currently set up shm_size
    # Suggestion  https://github.com/timescale/timescaledb-kubernetes/pull/131/files
    # 'shm_size': '8G'

    cpu_set_start, cpu_set_stop = map(int, cpu_set.split('-'))
    cpu_set = set(range(cpu_set_start, cpu_set_stop + 1))
    if gpu_set is not None:
        gpu_set = set(gpu_set.split(','))

    task_args = {
        'image': f'{REGISTRY_PULL_DOMAIN}/{image_name}:substra',
        'name': job_name,
        'cpu_set': cpu_set,
        'mem_limit': memory_limit_mb,
        'gpu_set': gpu_set,
        'command': command,
        'volumes': volumes,
        'label': task_label,
        'environment': environment
    }

    try:
        _k8s_compute(job_name, task_args, subtuple_key)
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

        # Handle local volume
        if 'local-' in path:
            volume_mounts.append({
                'name': 'local',
                'mountPath': bind['bind'],
                'subPath': path
            })
            volumes.append(
                {'name': 'local',
                 'persistentVolumeClaim': {'claimName': K8S_PVC['LOCAL_PVC']}}
            )
        else:
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

    k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)

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
    logger.info(f'Compute Pod {name} deleted.')


def k8s_get_or_create_local_volume(volume_id):
    pvc = K8S_PVC['LOCAL_PVC']
    logger.info(f'{volume_id} will be created in the PVC {pvc}')


def k8s_remove_local_volume(volume_id):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()
    job_name = f'clean-local-volume-{volume_id[:20]}'

    container = kubernetes.client.V1Container(
        name=job_name,
        security_context=get_security_context(SC_ON_CLEAN),
        image='busybox:1.31.1',
        command=['/bin/sh', '-c'],
        args=['rm -rvf /clean/*'],
        volume_mounts=[
            {'name': 'local',
             'mountPath': '/clean',
             'subPath': volume_id},

        ]
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
        containers=[container],
        affinity=pod_affinity,
        volumes=[
            {
                'name': 'local',
                'persistentVolumeClaim': {'claimName': K8S_PVC['LOCAL_PVC']}
            },
        ],
        security_context=get_pod_security_context(SC_ON_CLEAN)
    )

    pod = kubernetes.client.V1Pod(
        api_version='v1',
        kind='Pod',
        metadata=kubernetes.client.V1ObjectMeta(
            name=job_name,
            labels={'app': job_name, 'app.kubernetes.io/component': COMPONENT}
        ),
        spec=spec
    )

    k8s_client.create_namespaced_pod(body=pod, namespace=NAMESPACE)

    try:
        watch_pod(job_name)
    except Exception as e:
        logger.error(f'Cleaning failed, error: {e}')
    finally:
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


def get_security_context(enabled=True):
    if enabled:
        return kubernetes.client.V1SecurityContext(
            privileged=False,
            allow_privilege_escalation=False,
            capabilities=kubernetes.client.V1Capabilities(drop=['ALL']),
            run_as_non_root=True,
            run_as_group=int(RUN_AS_GROUP),
            run_as_user=int(RUN_AS_USER)
        )

    return None


def get_pod_security_context(enabled=True):
    if enabled:
        return kubernetes.client.V1PodSecurityContext(
            run_as_non_root=True,
            fs_group=int(FS_GROUP),
            run_as_group=int(RUN_AS_GROUP),
            run_as_user=int(RUN_AS_USER)
        )

    return None


def get_resources(task_args):

    r_requests = {
        'cpu': 1,
        'memory': '2000m'
    }

    # Disable for now, we let kubernetes decide
    r_limits = {
        'cpu': len(task_args['cpu_set']),
        'memory': task_args['mem_limit']
    }

    if task_args['gpu_set'] is not None:
        r_limits['nvidia.com/gpu'] = len(task_args['gpu_set'])

    return kubernetes.client.V1ResourceRequirements(
        limits=r_limits, requests=r_requests
    )
