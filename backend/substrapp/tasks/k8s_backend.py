import docker
import kubernetes
import time
import requests
import os
import logging

from substrapp.utils import get_remote_file
from kubernetes.stream import stream

logger = logging.getLogger(__name__)


MEDIA_ROOT = os.getenv('MEDIA_ROOT')
REGISTRY = os.getenv('REGISTRY')
REGISTRY_HOST = os.getenv('REGISTRY_HOST')
NAMESPACE = os.getenv('NAMESPACE')

K8S_PVC = {
    env_key: env_value for env_key, env_value in os.environ.items() if '_PVC' in env_key
}


class ImageNotFound(Exception):
    pass


class BuildError(Exception):
    pass


def watch_job(name):
    kubernetes.config.load_incluster_config()
    api = kubernetes.client.BatchV1Api()

    job = None
    finished = False

    while not finished:
        job = api.read_namespaced_job(name, NAMESPACE)

        if job.status.succeeded == job.spec.completions:
            finished = True
            logger.info(f'The job {NAMESPACE}/{name} succeeded')

        elif job.status.failed == job.spec.backoff_limit:
            logger.error(f'The job {NAMESPACE}/{name} failed')
            raise

        time.sleep(5)

    return job


def job_exists(name):
    kubernetes.config.load_incluster_config()
    api = kubernetes.client.BatchV1Api()

    try:
        api.read_namespaced_job(name, NAMESPACE)
    except Exception:
        return False
    else:
        return True


def wait_for_job_deletion(name):

    while job_exists(name):
        time.sleep(5)


def get_pod_name(name):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    pod = None

    while pod is None:
        api_response = k8s_client.list_namespaced_pod(
            NAMESPACE,
            label_selector=f'app={name}'
        )
        if api_response.items:
            pod = api_response.items.pop()

        time.sleep(5)

    return pod.metadata.name


def watch_pod(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    api_response = k8s_client.read_namespaced_pod(
        name=name,
        namespace=NAMESPACE,
        pretty=True
    )

    finished = False

    while not finished:
        api_response = k8s_client.read_namespaced_pod_status(
            name=name,
            namespace=NAMESPACE,
            pretty=True
        )

        if api_response.status.container_statuses:
            for container in api_response.status.container_statuses:
                finished = True if container.state.terminated is not None else False

        time.sleep(5)


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
        time.sleep(5)


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


def k8s_memory_limit(celery_worker_concurrency, celeryworker_image):
    docker_client = docker.from_env()
    # Get memory limit from docker container through the API
    # Because the docker execution may be remote

    memory_value = "int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 2))"

    cmd = f'python3 -u -c "import os; print({memory_value} // {celery_worker_concurrency}, end=\'\', flush=True)"'

    task_args = {
        'image': celeryworker_image,
        'command': cmd,
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
    }

    memory_limit_bytes = docker_client.containers.run(**task_args)

    return int(memory_limit_bytes)


def k8s_cpu_count(celeryworker_image):
    docker_client = docker.from_env()
    # Get CPU count from docker container through the API
    # Because the docker execution may be remote

    task_args = {
        'image': celeryworker_image,
        'command': 'python3 -u -c "import os; print(os.cpu_count())"',
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
    }

    cpu_count_bytes = docker_client.containers.run(**task_args).strip()

    return cpu_count_bytes


def k8s_gpu_list(celeryworker_image):
    docker_client = docker.from_env()
    # Get GPU list from docker container through the API
    # Because the docker execution may be remote

    cmd = 'python3 -u -c "import GPUtil as gputil;import json;'\
          'print(json.dumps([str(gpu.id) for gpu in gputil.getGPUs()]), end=\'\')"'

    task_args = {
        'image': celeryworker_image,
        'command': cmd,
        'detach': False,
        'stdout': True,
        'stderr': True,
        'auto_remove': False,
        'remove': True,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
        'environment': {'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
                        'NVIDIA_VISIBLE_DEVICES': 'all'},
        'runtime': 'nvidia'
    }

    gpu_list_bytes = docker_client.containers.run(**task_args)

    return gpu_list_bytes


def k8s_cpu_used(task_label):
    docker_client = docker.from_env()
    # Get CPU used from docker container through the API
    # Because the docker execution may be remote

    filters = {'status': 'running',
               'label': [task_label]}

    containers = [container.attrs
                  for container in docker_client.containers.list(filters=filters)]

    used_cpu_sets = [container['HostConfig']['CpusetCpus']
                     for container in containers
                     if container['HostConfig']['CpusetCpus']]

    return used_cpu_sets


def k8s_gpu_used(task_label):
    docker_client = docker.from_env()
    # Get GPU used from docker container through the API
    # Because the docker execution may be remote

    filters = {'status': 'running',
               'label': [task_label]}

    containers = [container.attrs
                  for container in docker_client.containers.list(filters=filters)]

    env_containers = [container['Config']['Env']
                      for container in containers]

    used_gpu_sets = []

    for env_list in env_containers:
        nvidia_env_var = [s.split('=')[1]
                          for s in env_list if "NVIDIA_VISIBLE_DEVICES" in s]

        used_gpu_sets.extend(nvidia_env_var)

    return used_gpu_sets


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

    dockerfile_fullpath = os.path.join(path, 'Dockerfile')

    dockerfile_mount_subpath = path.split('/subtuple/')[-1]

    container = kubernetes.client.V1Container(
        name=job_name,
        image='gcr.io/kaniko-project/executor:latest',
        args=[
            f'--dockerfile={dockerfile_fullpath}',
            f'--context=dir://{path}',
            f'--destination={REGISTRY}:5000/{tag}',
            f'--cache={str(not(rm)).lower()}',
            '--insecure'
        ],
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
        backoff_limit=4
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
        f'http://{REGISTRY}:5000/v2/{image_name}/manifests/latest',
        headers={'Accept': 'application/json'}
    )
    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    return response.json()


def k8s_delete_image(image_name):

    response = requests.get(
        f'http://{REGISTRY}:5000/v2/{image_name}/manifests/latest',
        headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
    )

    if response.status_code != requests.status_codes.codes.ok:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    digest = response.headers['Docker-Content-Digest']

    response = requests.delete(
        f'http://{REGISTRY}:5000/v2/{image_name}/manifests/{digest}',
        headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
    )
    if response.status_code != requests.status_codes.codes.accepted:
        raise ImageNotFound(f'Error when querying docker-registry, status code: {response.status_code}')

    return response


def k8s_get_or_create_local_volume(volume_id):

    docker_client = docker.from_env()

    try:
        docker_client.volumes.get(volume_id=volume_id)
    except docker.errors.NotFound:
        docker_client.volumes.create(name=volume_id)


def k8s_remove_local_volume(volume_id):

    docker_client = docker.from_env()

    try:
        local_volume = docker_client.volumes.get(volume_id=volume_id)
        local_volume.remove(force=True)
    except docker.errors.NotFound:
        pass
    except Exception:
        logger.error(f'Cannot remove volume {volume_id}', exc_info=True)


def k8s_remove_image(image_name):
    docker_client = docker.from_env()
    try:
        if docker_client.images.get(image_name):
            logger.info(f'Remove docker image {image_name}')
            docker_client.images.remove(image_name, force=True)

    except docker.errors.ImageNotFound:
        pass
    except docker.errors.APIError as e:
        logger.exception(e)


def k8s_compute(image_name, job_name, cpu_set, memory_limit_mb, command, volumes, task_label,
                capture_logs, environment, gpu_set, remove_image, subtuple_directory):

    # docker_client = docker.from_env()

    task_args = {
        'image': f'{REGISTRY_HOST}/{image_name}',
        'name': job_name,
        'cpuset_cpus': cpu_set,
        'mem_limit': memory_limit_mb,
        'command': command,
        'volumes': volumes,
        'shm_size': '8G',
        'labels': [task_label],
        'detach': False,
        'stdout': capture_logs,
        'stderr': capture_logs,
        'auto_remove': False,
        'remove': False,
        'network_disabled': True,
        'network_mode': 'none',
        'privileged': False,
        'cap_drop': ['ALL'],
        'environment': environment
    }

    if gpu_set is not None:
        task_args['environment'].update({'NVIDIA_VISIBLE_DEVICES': gpu_set})
        task_args['runtime'] = 'nvidia'

    k8s_job_name = job_name.replace("_", "-")

    try:
        ts = time.time()

        create_volume(k8s_job_name)
        create_nginx(k8s_job_name)
        create_compute_job(k8s_job_name, task_args)
        watch_job(k8s_job_name)

        # Fetch model and pred files
        fetch_outputs(f'nginx-{k8s_job_name}', subtuple_directory,
                      generate_filepaths(f'nginx-{k8s_job_name}'))
    finally:

        if capture_logs:
            container_format_log(
                k8s_job_name,
                get_pod_logs(name=get_pod_name(k8s_job_name),
                             container=k8s_job_name)
            )

        delete_compute_job(k8s_job_name)
        delete_nginx(k8s_job_name)
        delete_volume(k8s_job_name)

        # Remove images
        if remove_image:
            k8s_delete_image(image_name)

        elaps = (time.time() - ts) * 1000
        logger.info(f'k8s_client.images.run - elaps={elaps:.2f}ms')


def generate_filepaths(name):

    base_nginx = '/usr/share/nginx/html'

    volume_binds = [
        'output_model',
        'pred',
        'perf'
    ]

    filepaths = []
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    for bind in volume_binds:
        path = os.path.join(base_nginx, bind)
        exec_command = [
            '/bin/sh',
            '-c',
            f'ls {path}']

        api_response = stream(
            k8s_client.connect_get_namespaced_pod_exec,
            name,
            NAMESPACE,
            command=exec_command,
            stderr=True, stdin=True,
            stdout=True, tty=True
        )

        if api_response:
            files = [
                os.path.join(bind, file)
                for file in api_response.strip().split("\n")
            ]

            filepaths.extend(files)

    return filepaths


def generate_volumes(volume_binds, name):
    volume_mounts = []
    volumes = []

    for path, bind in volume_binds.items():
        # /HOST/PATH/servermedias/...
        if '/servermedias/' in path:
            volume_name = 'servermedias'
        # /HOST/PATH/medias/volume_name/...
        else:
            volume_name = path.split('/medias/')[-1].split('/')[0]

        if '/pred' in path and bind['mode'] == 'rw':
            volume_mounts.append({
                'name': name,
                'mountPath': bind['bind'],
                'subPath': 'pred'
            })
            # Volume will be added later, see volumes_rw
        elif '/output_model' in path and bind['mode'] == 'rw':
            volume_mounts.append({
                'name': name,
                'mountPath': bind['bind'],
                'subPath': 'output_model'
            })
            # Volume will be added later, see
        elif '/perf' in path and bind['mode'] == 'rw':
            volume_mounts.append({
                'name': name,
                'mountPath': bind['bind'],
                'subPath': 'perf'
            })
            # Volume will be added later, see volumes_rw
        else:
            subpath = path.split(f'/{volume_name}/')[-1]

            pvc_name = [key for key in K8S_PVC.keys()
                        if volume_name in key.lower()].pop()

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


def fetch_outputs(service_name, subtuple_directory, filepaths):
    for filepath in filepaths:
        content_dst_path = os.path.join(subtuple_directory, filepath)
        logger.info(f'Fetch http://{service_name}/{filepath} to {content_dst_path}')
        get_remote_file(
            url=f'http://{service_name}/{filepath}',
            auth=None,
            content_dst_path=content_dst_path,
            stream=True)


def create_compute_job(name, task_args):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.BatchV1Api()

    volumes_rw = [
        {'name': name,
         'persistentVolumeClaim': {'claimName': name}},
    ]

    volume_mounts, volumes = generate_volumes(task_args['volumes'], name)

    # Should be in a job as it will end
    container_compute = kubernetes.client.V1Container(
        name=name,
        image=task_args['image'],
        args=task_args['command'].split(" ") if task_args['command'] is not None else None,
        volume_mounts=volume_mounts
        # resources=kubernetes.client.V1ResourceRequirements(
        #     limits={'cpu': len(task_args['cpuset_cpus']), 'memory': task_args['mem_limit']}
        # )
    )

    # Create and configurate a spec section
    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(labels={'app': name}),
        spec=kubernetes.client.V1PodSpec(
            restart_policy='Never',
            containers=[container_compute],
            volumes=volumes + volumes_rw
        )
    )

    spec = kubernetes.client.V1JobSpec(
        template=template,
        backoff_limit=4
    )

    job = kubernetes.client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=spec
    )

    k8s_client.create_namespaced_job(body=job, namespace=NAMESPACE)


def create_nginx(name):
    create_nginx_pod(name)
    create_nginx_service(name)


def delete_nginx(name):
    delete_pod(f'nginx-{name}')
    delete_nginx_service(name)


def create_nginx_pod(name):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    volumes_rw = [
        {'name': name,
         'persistentVolumeClaim': {'claimName': name}},

    ]

    container_nginx = kubernetes.client.V1Container(
        name=f'nginx-{name}',
        image='nginx:1.17.10',
        ports=[kubernetes.client.V1ContainerPort(container_port=80)],
        volume_mounts=[
            {'name': name,
             'mountPath': '/usr/share/nginx/html/output_model',
             'subPath': 'output_model',
             'readOnly': True},
            {'name': name,
             'mountPath': '/usr/share/nginx/html/pred',
             'subPath': 'pred',
             'readOnly': True},
            {'name': name,
             'mountPath': '/usr/share/nginx/html/perf',
             'subPath': 'perf',
             'readOnly': True},
        ]
        # resources=kubernetes.client.V1ResourceRequirements(
        #     requests={'cpu': '100m', 'memory': '200Mi'},
        #     limits={'cpu': '500m', 'memory': '500Mi'}
        # )
    )

    spec = kubernetes.client.V1PodSpec(
        containers=[container_nginx],
        volumes=volumes_rw
    )

    # Instantiate the pod object
    pod = kubernetes.client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=kubernetes.client.V1ObjectMeta(name=f'nginx-{name}', labels={'app': f'nginx-{name}'}),
        spec=spec
    )

    # Create pod
    k8s_client.create_namespaced_pod(
        body=pod,
        namespace=NAMESPACE
    )

    print(f"Pod {name} created.")


def delete_compute_job(name):

    if job_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.BatchV1Api()

        k8s_client.delete_namespaced_job(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    wait_for_job_deletion(name)
    logger.info(f'Compute Job {name} deleted.')


def delete_pod(name):

    if pod_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.CoreV1Api()

        api_response = k8s_client.delete_namespaced_pod(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    wait_for_pod_deletion(name)
    logger.info(f"Pod {name} deleted.")

    if api_response.status == 'Failure':
        raise Exception(f'Failed to delete Pod {name}.')


def create_nginx_service(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(name=f'nginx-{name}'),
        spec=kubernetes.client.V1ServiceSpec(
            type="ClusterIP",
            ports=[kubernetes.client.V1ServicePort(name="http", protocol="TCP", port=80, target_port=80)],
            selector={'app': f'nginx-{name}'}
        )
    )

    k8s_client.create_namespaced_service(namespace=NAMESPACE, body=service)

    logger.info(f'Service nginx-{name} created.')


def service_exists(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    try:
        k8s_client.read_namespaced_service(
            name=name,
            namespace=NAMESPACE)
    except Exception:
        return False
    else:
        return True


def wait_for_service_deletion(name):
    while service_exists(name):
        time.sleep(5)


def delete_nginx_service(name):

    if service_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.CoreV1Api()

        k8s_client.delete_namespaced_service(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    wait_for_service_deletion(name)
    logger.info(f'Service nginx-{name} deleted.')


def create_volume(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    pvc = kubernetes.client.V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=kubernetes.client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteOnce"],
            resources={
                "requests": {"storage": "10Gi"}
            },
        )
    )

    k8s_client.create_namespaced_persistent_volume_claim(NAMESPACE, body=pvc)

    logger.info(f'PVC {name} created.')


def pvc_exists(name):
    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    try:
        k8s_client.read_namespaced_persistent_volume_claim(
            name=name,
            namespace=NAMESPACE)
    except Exception:
        return False
    else:
        return True


def wait_for_pvc_deletion(name):
    while pvc_exists(name):
        time.sleep(5)


def delete_volume(name):

    if pvc_exists(name):
        kubernetes.config.load_incluster_config()
        k8s_client = kubernetes.client.CoreV1Api()

        k8s_client.delete_namespaced_persistent_volume_claim(
            name=name,
            namespace=NAMESPACE,
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    wait_for_pvc_deletion(name)
    logger.info(f'PVC {name} deleted.')
