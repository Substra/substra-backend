from pathlib import Path

import docker
import pytest


@pytest.fixture(scope="session")
def ubuntu_base_image():
    return "ubuntu:mantic-20230926"


@pytest.fixture(scope="session")
def tag_ubuntu_custom_image():
    return "ubuntu:augmented"


@pytest.fixture(scope="session")
def base_registry_local_port():
    return 5555


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


def transfer_to_base_registry(image_name, docker_client, base_registry_local_port):
    # we transfer the image to the local registry
    image = docker_client.images.pull(image_name)
    new_name = f"localhost:{base_registry_local_port}/{image_name}"
    image.tag(new_name)
    docker_client.images.push(new_name)


@pytest.fixture(scope="session", autouse=True)
def initialize_local_registry(docker_client, ubuntu_base_image, tag_ubuntu_custom_image, base_registry_local_port):
    # we create a local registry and add a docker image to it
    base_registry = docker_client.containers.run(
        "registry:2",
        detach=True,
        ports={"5000/tcp": base_registry_local_port},
        name="image-transfer-test-registry",
    )
    transfer_to_base_registry(ubuntu_base_image, docker_client, base_registry_local_port)
    # transfer_to_base_registry("busybox:1.36.1", docker_client, base_registry_local_port)

    image, _ = docker_client.images.build(
        path=str(Path(__file__).parent),
        tag=f"localhost:{base_registry_local_port}/{tag_ubuntu_custom_image}",
    )
    docker_client.images.push(image.tags[0])

    yield
    base_registry.remove(force=True, v=True)
