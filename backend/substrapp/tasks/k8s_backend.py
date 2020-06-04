import math
import kubernetes
import time
import requests
import os
import logging


from substrapp.utils import get_subtuple_directory, timeit
from distutils.dir_util import copy_tree


logger = logging.getLogger(__name__)


MEDIA_ROOT = os.getenv('MEDIA_ROOT')
REGISTRY = os.getenv('REGISTRY')
REGISTRY_SCHEME = os.getenv('REGISTRY_SCHEME')
REGISTRY_PULL_DOMAIN = os.getenv('REGISTRY_PULL_DOMAIN')
NAMESPACE = os.getenv('NAMESPACE')
NODE_NAME = os.getenv('NODE_NAME')

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

    return max(1, math.floor(float(node.status.capacity['cpu'])))


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


def watch_job(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()

    job = None
    finished = False

    while not finished:
        job = k8s_client.read_namespaced_job(name, NAMESPACE)

        if job.status.succeeded and job.status.succeeded >= job.spec.completions:
            finished = True
            logger.info(f'The job {NAMESPACE}/{name} succeeded')

        elif job.status.failed and job.status.failed >= job.spec.backoff_limit:
            logger.error(f'The job {NAMESPACE}/{name} failed')
            raise Exception(f'The job {NAMESPACE}/{name} failed')

        if not finished:
            time.sleep(0.5)

    return job


def job_exists(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()

    try:
        k8s_client.read_namespaced_job(name, NAMESPACE)
    except Exception:
        return False
    else:
        return True


def wait_for_job_deletion(name):

    while job_exists(name):
        pass


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


def get_pod_logs(name, container):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    logs = f'No pod {name}'

    if pod_exists(name):
        logs = k8s_client.read_namespaced_pod_log(
            name=name,
            namespace=NAMESPACE,
            container=container
        )

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
    k8s_client = kubernetes.client.BatchV1Api()

    job_name = f'kaniko-{tag.split("/")[-1].replace("_", "-")}'

    logger.info(f'The job {NAMESPACE}/{job_name} started')

    dockerfile_fullpath = os.path.join(path, 'Dockerfile')

    dockerfile_mount_subpath = path.split('/subtuple/')[-1]

    args = [
        f'--dockerfile={dockerfile_fullpath}',
        f'--context=dir://{path}',
        f'--destination={REGISTRY}/{tag}',
        f'--cache={str(not(rm)).lower()}'
    ]

    if REGISTRY_SCHEME == 'http':
        args.append('--insecure')

    container = kubernetes.client.V1Container(
        name=job_name,
        image='gcr.io/kaniko-project/executor:latest',
        args=args,
        volume_mounts=[
            {'name': 'dockerfile',
             'mountPath': path,
             'subPath': dockerfile_mount_subpath,
             'readOnly': True},

            {'name': 'cache',
             'mountPath': '/cache',
             'readOnly': True}
        ]
    )

    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(labels={'app': job_name}),
        spec=kubernetes.client.V1PodSpec(
            restart_policy='Never',
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
            ]
        )
    )

    spec = kubernetes.client.V1JobSpec(
        template=template,
        backoff_limit=2
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=job_name),
        spec=spec
    )

    k8s_client.create_namespaced_job(body=job, namespace=NAMESPACE)

    try:
        watch_job(job_name)
    except Exception as e:
        logger.error(f'Kaniko build failed, error: {e}')
        raise BuildError(f'Kaniko build failed, error: {e}')
    finally:
        k8s_client.delete_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )


def k8s_get_image(image_name):
    response = requests.get(
        f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/latest',
        headers={'Accept': 'application/json'}
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    return response.json()


def k8s_remove_image(image_name):

    try:
        response = requests.get(
            f'{REGISTRY_SCHEME}://{REGISTRY}/v2/{image_name}/manifests/latest',
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
                capture_logs, environment, gpu_set, remove_image, subtuple_key):

    # We cannot currently set up shm_size
    # Suggestion  https://github.com/timescale/timescaledb-kubernetes/pull/131/files
    # 'shm_size': '8G'

    cpu_set_start, cpu_set_stop = map(int, cpu_set.split('-'))
    cpu_set = set(range(cpu_set_start, cpu_set_stop + 1))
    if gpu_set is not None:
        gpu_set = set(gpu_set.split(','))

    task_args = {
        'image': f'{REGISTRY_PULL_DOMAIN}/{image_name}',
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
        copy_outputs(subtuple_key)
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

        delete_compute_job(job_name)
        clean_outputs(subtuple_key)

        # Remove images
        if remove_image:
            k8s_remove_image(image_name)


def generate_volumes(volume_binds, name, subtuple_key):
    volume_mounts = []
    volumes = []

    for path, bind in volume_binds.items():

        volume_processed = False

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

            volume_processed = True

        # Handle outputs paths which need to be writable
        for subpath in ['/pred', '/output_model', '/perf', '/export']:
            if subpath in path and bind['mode'] == 'rw':
                volume_mounts.append({
                    'name': 'outputs',
                    'mountPath': bind['bind'],
                    'subPath': f'{subtuple_key}{subpath}'
                })
                volumes.append(
                    {'name': 'outputs',
                     'persistentVolumeClaim': {'claimName': K8S_PVC['OUTPUTS_PVC']}}
                )

                volume_processed = True

        if not volume_processed:
            # Handle read-only paths

            # /HOST/PATH/servermedias/...
            if '/servermedias/' in path:
                volume_name = 'servermedias'
            # /HOST/PATH/medias/volume_name/...
            else:
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
                'readOnly': True

            })

            volumes.append({
                'name': volume_name,
                'persistentVolumeClaim': {'claimName': K8S_PVC[pvc_name]}
            })

    # Unique volumes
    volumes = list({v['name']: v for v in volumes}.values())

    return volume_mounts, volumes


def copy_outputs(subtuple_key):
    subtuple_directory = get_subtuple_directory(subtuple_key)
    for output_folder in ['output_model', 'pred', 'perf', 'export']:
        content_dst_path = os.path.join(subtuple_directory, output_folder)
        content_path = content_dst_path.replace('subtuple', 'outputs')
        if os.path.exists(content_path):
            logger.info(f'Copy {content_path} to {content_dst_path}')
            copy_tree(content_path, content_dst_path)


def clean_outputs(subtuple_key):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()
    job_name = f'clean-outputs-{subtuple_key[:10]}'

    container = kubernetes.client.V1Container(
        name=job_name,
        image='busybox',
        args=['rm',
              '-rf',
              f'/clean/{subtuple_key}'],
        volume_mounts=[
            {'name': 'outputs',
             'mountPath': '/clean',
             'subPath': subtuple_key},

        ]
    )

    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(labels={'app': job_name}),
        spec=kubernetes.client.V1PodSpec(
            restart_policy='Never',
            containers=[container],
            volumes=[
                {
                    'name': 'outputs',
                    'persistentVolumeClaim': {'claimName': K8S_PVC['OUTPUTS_PVC']}
                },
            ]
        )
    )

    spec = kubernetes.client.V1JobSpec(
        template=template,
        backoff_limit=0
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=job_name),
        spec=spec
    )

    k8s_client.create_namespaced_job(body=job, namespace=NAMESPACE)

    try:
        watch_job(job_name)
    except Exception as e:
        logger.error(f'Cleaning failed, error: {e}')
    finally:
        k8s_client.delete_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )


def _k8s_compute(name, task_args, subtuple_key):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()

    volume_mounts, volumes = generate_volumes(task_args['volumes'], name, subtuple_key)

    # Resources

    # Set minimal requests
    r_requests = {
        'cpu': 2,
        'memory': '2000m'
    }

    r_limits = {
        'cpu': len(task_args['cpu_set']),
        'memory': task_args['mem_limit']
    }

    if task_args['gpu_set'] is not None:
        r_limits['nvidia.com/gpu'] = len(task_args['gpu_set'])

    resources = kubernetes.client.V1ResourceRequirements(
        limits=r_limits, requests=r_requests
    )

    # security
    security_context = kubernetes.client.V1SecurityContext(
        privileged=False,
        allow_privilege_escalation=False,
        capabilities=kubernetes.client.V1Capabilities(drop=['ALL']),
    )

    container_compute = kubernetes.client.V1Container(
        name=name,
        image=task_args['image'],
        args=task_args['command'].split(" ") if task_args['command'] is not None else None,
        volume_mounts=volume_mounts,
        resources=resources,
        security_context=security_context
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

    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(name=name,
                                                labels={'app': name,
                                                        'task': task_args['label']}
                                                ),
        spec=kubernetes.client.V1PodSpec(
            restart_policy='Never',
            affinity=pod_affinity,
            containers=[container_compute],
            volumes=volumes
        )
    )

    spec = kubernetes.client.V1JobSpec(
        template=template,
        backoff_limit=0
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=name,
                                                labels={'app': name,
                                                        'task': task_args['label']}
                                                ),
        spec=spec
    )

    k8s_client.create_namespaced_job(body=job, namespace=NAMESPACE)

    watch_job(name)


def delete_compute_job(name):

    if job_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.BatchV1Api()

        k8s_client.delete_namespaced_job(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=0
            )
        )

    wait_for_job_deletion(name)
    logger.info(f'Compute Job {name} deleted.')


def k8s_get_or_create_local_volume(volume_id):
    pvc = K8S_PVC['LOCAL_PVC']
    logger.info(f'{volume_id} will be created in the PVC {pvc}')


def k8s_remove_local_volume(volume_id):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()
    job_name = f'clean-outputs-{volume_id[:20]}'

    container = kubernetes.client.V1Container(
        name=job_name,
        image='busybox',
        args=['rm',
              '-rf',
              f'/clean/{volume_id}'],
        volume_mounts=[
            {'name': 'local',
             'mountPath': '/clean',
             'subPath': volume_id},

        ]
    )

    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(labels={'app': job_name}),
        spec=kubernetes.client.V1PodSpec(
            restart_policy='Never',
            containers=[container],
            volumes=[
                {
                    'name': 'local',
                    'persistentVolumeClaim': {'claimName': K8S_PVC['LOCAL_PVC']}
                },
            ]
        )
    )

    spec = kubernetes.client.V1JobSpec(
        template=template,
        backoff_limit=0
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=job_name),
        spec=spec
    )

    k8s_client.create_namespaced_job(body=job, namespace=NAMESPACE)

    try:
        watch_job(job_name)
    except Exception as e:
        logger.error(f'Cleaning failed, error: {e}')
    finally:
        k8s_client.delete_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )
