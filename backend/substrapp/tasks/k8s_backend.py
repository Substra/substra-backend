import docker
import kubernetes
import time
import requests
import os
import logging
logger = logging.getLogger(__name__)


REGISTRY = os.getenv('REGISTRY')
REGISTRY_HOST = os.getenv('REGISTRY_HOST')
NAMESPACE = os.getenv('NAMESPACE')

K8S_PVC = {
    env_key: env_value for env_key, env_value in os.environ if '_PVC' in env_key
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


def get_pod_logs(name, container):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    return k8s_client.read_namespaced_pod_log(
        name=name,
        namespace=NAMESPACE,
        container=container
    )


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
                capture_logs, environment, gpu_set, remove_image, subtuple_key):

    docker_client = docker.from_env()

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
    pod_name = None
    try:
        ts = time.time()

        # DOCKER
        docker_client.containers.run(**task_args)

        # K8S
        deployment = create_deployment_object(k8s_job_name, task_args, subtuple_key)
        create_deployment(deployment)
        pod_name = get_pod_name(k8s_job_name)
        watch_pod(pod_name)
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        # we need to remove the containers to be able to remove the local
        # volume in case of compute plan
        container = docker_client.containers.get(job_name)
        if capture_logs:
            container_format_log(
                job_name,
                container.logs()
            )
            if pod_name is not None:
                container_format_log(
                    k8s_job_name,
                    get_pod_logs(name=pod_name,
                                 container=k8s_job_name)
                )
        container.remove()

        delete_deployment(k8s_job_name)

        # Remove images
        if remove_image:
            k8s_delete_image(image_name)

        elaps = (time.time() - ts) * 1000
        logger.info(f'docker_client.images.run - elaps={elaps:.2f}ms')


def create_deployment_object(name, task_args, subtuple_key):

    print(task_args['volumes'])

    # Configureate Pod template container
    container_nginx = kubernetes.client.V1Container(
        name='nginx',
        image='nginx:1.17.10',
        ports=[kubernetes.client.V1ContainerPort(container_port=80)],
        # resources=kubernetes.client.V1ResourceRequirements(
        #     requests={'cpu': '100m', 'memory': '200Mi'},
        #     limits={'cpu': '500m', 'memory': '500Mi'}
        # )
    )

    container_compute = kubernetes.client.V1Container(
        name=name,
        image=task_args['image'],
        args=task_args['command'].split(" ") if task_args['command'] is not None else None,
        volume_mounts=[
            {'name': 'subtuple',
             'mountPath': '/sandbox/',
             'subPath': subtuple_key,
             'readOnly': True}
        ]

        # resources=kubernetes.client.V1ResourceRequirements(
        #     limits={'cpu': len(task_args['cpuset_cpus']), 'memory': task_args['mem_limit']}
        # )
    )

    # Create and configurate a spec section
    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(labels={'app': name}),
        spec=kubernetes.client.V1PodSpec(
            containers=[container_compute, container_nginx],
            volumes=[
                {
                    'name': 'subtuple',
                    'persistentVolumeClaim': {'claimName': K8S_PVC['SUBTUPLE_PVC']}
                }
            ]
        )
    )

    # Create the specification of deployment
    spec = kubernetes.client.V1DeploymentSpec(
        replicas=1,
        template=template,
        selector={'matchLabels': {'app': name}})
    # Instantiate the deployment object
    deployment = kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=spec)

    return deployment


def create_deployment(deployment):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.AppsV1Api()

    k8s_client.create_namespaced_deployment(
        body=deployment,
        namespace=NAMESPACE
    )

    logger.info(f'Deployment {deployment.metadata.name} created.')


def delete_deployment(name):

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.AppsV1Api()

    k8s_client.delete_namespaced_deployment(
        name=name,
        namespace=NAMESPACE,
        body=kubernetes.client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )
    )

    logger.info(f'Deployment {name} deleted.')
