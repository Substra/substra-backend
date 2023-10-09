from zipfile import ZipFile

import pytest

from image_transfer.decoder import push_payload
from image_transfer.encoder import make_payload
from image_transfer.exceptions import ManifestContentError
from image_transfer.exceptions import ManifestNotFoundError


@pytest.fixture(scope="session")
def destination_registry_local_port():
    return 5556


@pytest.fixture
def add_destination_registry(docker_client, destination_registry_local_port):
    destination_registry = docker_client.containers.run(
        "registry:2",
        detach=True,
        ports={"5000/tcp": destination_registry_local_port},
        name="image-transfer-test-registry-destination",
    )
    yield
    destination_registry.remove(force=True, v=True)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_end_to_end_single_image(
    docker_client, tmp_path, ubuntu_base_image, base_registry_local_port, destination_registry_local_port
):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    images_pushed = push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)
    assert images_pushed == [ubuntu_base_image]
    # we make sure the docker image exists in the registry and is working
    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", ["echo", "do"], remove=True
        )
        == b"do\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", force=True)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_end_to_end_multiple_images(
    tmp_path,
    docker_client,
    ubuntu_base_image,
    tag_ubuntu_custom_image,
    base_registry_local_port,
    destination_registry_local_port,
):
    payload_path = tmp_path / "payload.zip"

    make_payload(
        payload_path,
        [ubuntu_base_image, tag_ubuntu_custom_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)

    # we make sure the docker image exists in the registry and is working
    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", ["echo", "do"], remove=True
        )
        == b"do\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", force=True)

    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/{tag_ubuntu_custom_image}",
            ["cat", "/hello-world.txt"],
            remove=True,
        )
        == b"hello-world\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/{tag_ubuntu_custom_image}", force=True)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_end_to_end_single_image_from_dockerhub_no_platform(
    tmp_path,
    ubuntu_base_image,
):
    payload_path = tmp_path / "payload.zip"
    with pytest.raises(ManifestContentError):
        make_payload(payload_path, [f"library/{ubuntu_base_image}"])


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_end_to_end_single_image_from_dockerhub(
    tmp_path,
    docker_client,
    ubuntu_base_image,
    destination_registry_local_port,
):
    payload_path = tmp_path / "payload.zip"
    make_payload(payload_path, [f"library/{ubuntu_base_image}"], platform="linux/amd64")

    images_pushed = push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)
    assert images_pushed == [f"library/{ubuntu_base_image}"]

    # we make sure the docker image exists in the registry and is working
    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/library/{ubuntu_base_image}", ["echo", "do"], remove=True
        )
        == b"do\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/library/{ubuntu_base_image}", force=True)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_end_to_end_only_necessary_layers(
    tmp_path,
    docker_client,
    ubuntu_base_image,
    tag_ubuntu_custom_image,
    base_registry_local_port,
    destination_registry_local_port,
):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)

    # the ubuntu base image is now in the registry. We can make a payload for the
    # augmented version, and it has a lot of layers in common
    payload_path.unlink()
    make_payload(
        payload_path,
        [tag_ubuntu_custom_image],
        docker_images_already_transferred=[ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    # we make sure that only two blobs are in the zip: the image configuration
    # and the layer that is common to both images
    all_blobs = []
    with ZipFile(payload_path) as zip_file:
        for name in zip_file.namelist():
            if name.startswith("blobs/"):
                all_blobs.append(name)
    assert len(all_blobs) == 2

    # we load the payload and make sure the augmented version is working
    images_loaded = push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)
    assert images_loaded == [tag_ubuntu_custom_image]

    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", ["echo", "do"], remove=True
        )
        == b"do\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/{ubuntu_base_image}", force=True)

    assert (
        docker_client.containers.run(
            f"localhost:{destination_registry_local_port}/{tag_ubuntu_custom_image}",
            ["cat", "/hello-world.txt"],
            remove=True,
        )
        == b"hello-world\n"
    )
    docker_client.images.remove(f"localhost:{destination_registry_local_port}/{tag_ubuntu_custom_image}", force=True)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_image_skipped_is_still_declared_in_the_payload(
    tmp_path,
    ubuntu_base_image,
    tag_ubuntu_custom_image,
    base_registry_local_port,
    destination_registry_local_port,
):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    images_pushed = push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)
    assert images_pushed == [ubuntu_base_image]

    payload_path.unlink()

    make_payload(
        payload_path,
        [ubuntu_base_image, tag_ubuntu_custom_image],
        docker_images_already_transferred=[ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    # we make sure that only two blobs are in the zip: the image configuration
    # and the layer that is common to both images
    all_blobs = []
    with ZipFile(payload_path) as zip_file:
        for name in zip_file.namelist():
            if name.startswith("blobs/"):
                all_blobs.append(name)
    assert len(all_blobs) == 2

    images_pushed = push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)
    assert set(images_pushed) == {ubuntu_base_image, tag_ubuntu_custom_image}


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_raise_error_if_image_is_not_here_and_strict(
    tmp_path, tag_ubuntu_custom_image, base_registry_local_port, destination_registry_local_port
):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [tag_ubuntu_custom_image],
        docker_images_already_transferred=[tag_ubuntu_custom_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    with pytest.raises(ManifestNotFoundError) as err:
        push_payload(payload_path, strict=True, registry=f"localhost:{destination_registry_local_port}", secure=False)

    assert tag_ubuntu_custom_image in str(err.value)


@pytest.mark.usefixtures("add_destination_registry")
@pytest.mark.serial
def test_warning_if_image_is_not_here(
    tmp_path, tag_ubuntu_custom_image, base_registry_local_port, destination_registry_local_port
):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [tag_ubuntu_custom_image],
        docker_images_already_transferred=[tag_ubuntu_custom_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    with pytest.warns(UserWarning) as record:
        push_payload(payload_path, registry=f"localhost:{destination_registry_local_port}", secure=False)

    assert tag_ubuntu_custom_image in str(record[0].message)
