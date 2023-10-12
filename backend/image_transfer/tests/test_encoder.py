import json

import pytest
from dxf import DXFBase

from image_transfer.decoder import push_payload
from image_transfer.encoder import get_manifest_and_list_of_blobs_to_pull
from image_transfer.encoder import make_payload


@pytest.mark.serial
def test_end_to_end_single_image(tmp_path, docker_client, ubuntu_base_image, base_registry_local_port):
    payload_path = tmp_path / "payload.zip"
    make_payload(
        payload_path,
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    images_pushed = push_payload(payload_path, registry=f"localhost:{base_registry_local_port}", secure=False)
    assert images_pushed == [ubuntu_base_image]
    # we make sure the docker image exists in the registry and is working
    docker_client.images.remove(f"localhost:{base_registry_local_port}/{ubuntu_base_image}", force=True)
    assert (
        docker_client.containers.run(
            f"localhost:{base_registry_local_port}/{ubuntu_base_image}", ["echo", "do"], remove=True
        )
        == b"do\n"
    )


@pytest.mark.serial
def test_get_manifest_and_list_of_all_blob(base_registry_local_port, ubuntu_base_image):
    dxf_base = DXFBase(f"localhost:{base_registry_local_port}", insecure=True)
    manifest, blobs = get_manifest_and_list_of_blobs_to_pull(dxf_base, ubuntu_base_image)
    assert json.loads(manifest.content) == {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 2299,
            "digest": "sha256:1d8801a7ecb54952ea17852be887c1d858fd7bd78dcee093afc11fee7ed53f7c",
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": 28079281,
                "digest": "sha256:70c34fc37a9391a001a8d99c74b27823143398763bcd623c3402a790006947ea",
            }
        ],
    }

    assert len(blobs) == 2
    for blob in blobs:
        assert blob.repository == "ubuntu"
        assert blob.digest in manifest.content


@pytest.mark.serial
def test_make_payload_from_path(tmp_path, ubuntu_base_image, base_registry_local_port):
    zip_path = tmp_path / "test.zip"

    make_payload(
        zip_path,
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )

    assert zip_path.exists()
    assert zip_path.stat().st_size > 1024


@pytest.mark.serial
def test_make_payload_from_str(tmp_path, ubuntu_base_image, base_registry_local_port):
    zip_path = tmp_path / "test.zip"

    make_payload(
        str(zip_path),
        [ubuntu_base_image],
        registry=f"localhost:{base_registry_local_port}",
        secure=False,
    )
    assert zip_path.exists()
    assert zip_path.stat().st_size > 1024


@pytest.mark.serial
def test_make_payload_from_opened_file(tmp_path, ubuntu_base_image, base_registry_local_port):
    zip_path = tmp_path / "test.zip"
    with open(zip_path, "wb") as f:
        make_payload(f, [ubuntu_base_image], registry=f"localhost:{base_registry_local_port}", secure=False)

    assert zip_path.exists()
    assert zip_path.stat().st_size > 1024
