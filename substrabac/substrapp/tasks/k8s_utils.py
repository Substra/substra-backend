from kubernetes import client
import time


def create_pod(k8s_client, namespace, name, image, command, labels):

    container = client.V1Container(
        name=name,
        image=image,
        args=command.split(" "),
        image_pull_policy='Never'
    )

    spec = client.V1PodSpec(restart_policy="Never",
                            containers=[container])

    # Instantiate the pod object
    pod = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(name=name),
        spec=spec
    )

    # Create pod
    api_response = k8s_client.create_namespaced_pod(
        body=pod,
        namespace=namespace
    )

    print(f"Pod {name} created.\n{api_response}")


def wait_pod(k8s_client, namespace, name):

    api_response = k8s_client.read_namespaced_pod(
        name=name,
        namespace=namespace,
        pretty=True
    )
    print(f"Pod read.\n{api_response}")

    finished = False

    while not finished:
        api_response = k8s_client.read_namespaced_pod_status(
            name=name,
            namespace=namespace,
            pretty=True
        )
        print(f"Pod {name} read status.\n{api_response.status.container_statuses}")

        if api_response.status.container_statuses:
            container = api_response.status.container_statuses[0]  # There is only one container
            finished = True if container.state.terminated is not None else False

        time.sleep(1)


def get_pod_logs(k8s_client, namespace, name):
    return k8s_client.read_namespaced_pod_log(name, namespace)


def delete_pod(k8s_client, namespace, name):

    api_response = k8s_client.delete_namespaced_pod(
        name=name,
        namespace=namespace,
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )
    )

    print(f"Pod deleted.\n{api_response}")

    if api_response.status == 'Failure':
        raise Exception(f'Failed to delete pod {name} in the namespace {namespace}')
