from __future__ import annotations

import sys
from pathlib import Path
from typing import IO
from typing import Iterator
from typing import Optional
from typing import Union

from dxf import DXF
from dxf import DXFBase
from tqdm import tqdm

from image_transfer.common import Authenticator
from image_transfer.common import Blob
from image_transfer.common import BlobLocationInRegistry
from image_transfer.common import BlobPathInZip
from image_transfer.common import Manifest
from image_transfer.common import PayloadDescriptor
from image_transfer.common import PayloadSide
from image_transfer.common import progress_as_string
from substrapp.utils import safezip


def add_blobs_to_zip(
    dxf_base: DXFBase,
    zip_file: safezip.ZipFile,
    blobs_to_pull: list[Blob],
    blobs_already_transferred: list[Blob],
) -> dict[str, Union[BlobPathInZip, BlobLocationInRegistry]]:
    blobs_paths = {}
    for blob_index, blob in enumerate(blobs_to_pull):
        print(progress_as_string(blob_index, blobs_to_pull), end=" ", file=sys.stderr)
        if blob.digest in blobs_paths:
            print(
                f"Skipping {blob} because it's in {blobs_paths[blob.digest]}",
                file=sys.stderr,
            )
            continue

        if dest_blob := get_blob_with_same_digest(blobs_already_transferred, blob.digest):
            print(
                f"Skipping {blob} because it's already in the destination registry "
                f"in the repository {dest_blob.repository}",
                file=sys.stderr,
            )
            blobs_paths[blob.digest] = BlobLocationInRegistry(repository=dest_blob.repository)
            continue

        # nominal case
        print(f"Pulling blob {blob} and storing it in the zip", file=sys.stderr)
        blob_path_in_zip = download_blob_to_zip(dxf_base, blob, zip_file)
        blobs_paths[blob.digest] = BlobPathInZip(zip_path=blob_path_in_zip)
    return blobs_paths


def download_blob_to_zip(dxf_base: DXFBase, blob: Blob, zip_file: safezip.ZipFile):
    repository_dxf = DXF.from_base(dxf_base, blob.repository)
    bytes_iterator, total_size = repository_dxf.pull_blob(blob.digest, size=True)

    # we write the blob directly to the zip file
    with tqdm(total=total_size, unit="B", unit_scale=True) as pbar:
        blob_path_in_zip = f"blobs/{blob.digest}"
        with zip_file.open(blob_path_in_zip, "w", force_zip64=True) as blob_in_zip:
            for chunk in bytes_iterator:
                blob_in_zip.write(chunk)
                pbar.update(len(chunk))
    return blob_path_in_zip


def get_blob_with_same_digest(list_of_blobs: list[Blob], digest: str) -> Optional[Blob]:
    for blob in list_of_blobs:
        if blob.digest == digest:
            return blob


def get_manifest_and_list_of_blobs_to_pull(
    dxf_base: DXFBase,
    docker_image: str,
    platform: Optional[str] = None,
) -> tuple[Manifest, list[Blob]]:
    manifest = Manifest(dxf_base, docker_image, PayloadSide.ENCODER, platform=platform)
    return manifest, manifest.get_list_of_blobs()


def get_manifests_and_list_of_all_blobs(
    dxf_base: DXFBase, docker_images: Iterator[str], platform: Optional[str] = None
) -> tuple[list[Manifest], list[Blob]]:
    manifests = []
    blobs_to_pull = []
    for docker_image in docker_images:
        manifest, blobs = get_manifest_and_list_of_blobs_to_pull(dxf_base, docker_image, platform)
        manifests.append(manifest)
        blobs_to_pull += blobs
    return manifests, blobs_to_pull


def create_zip_from_docker_images(
    dxf_base: DXFBase,
    docker_images_to_transfer: list[str],
    docker_images_already_transferred: list[str],
    zip_file: safezip.ZipFile,
    platform: Optional[str] = None,
) -> None:
    payload_descriptor = PayloadDescriptor.from_images(docker_images_to_transfer, docker_images_already_transferred)

    manifests, blobs_to_pull = get_manifests_and_list_of_all_blobs(
        dxf_base, payload_descriptor.get_images_not_transferred_yet(), platform=platform
    )
    _, blobs_already_transferred = get_manifests_and_list_of_all_blobs(
        dxf_base, docker_images_already_transferred, platform=platform
    )
    payload_descriptor.blobs_paths = add_blobs_to_zip(dxf_base, zip_file, blobs_to_pull, blobs_already_transferred)
    for manifest in manifests:
        dest = payload_descriptor.manifests_paths[manifest.docker_image_name]
        zip_file.writestr(dest, manifest.content)

    zip_file.writestr("payload_descriptor.json", payload_descriptor.model_dump_json(indent=4))


def make_payload(
    zip_file: Union[IO, Path, str],
    docker_images_to_transfer: list[str],
    docker_images_already_transferred: Optional[list[str]] = None,
    registry: str = "registry-1.docker.io",
    secure: bool = True,
    platform: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """
    Creates a payload from a list of docker images
    All the docker images must be in the same registry.

    Args:
        zip_file: The path to the zip file to create. It can be a `pathlib.Path` or
            a `str`. It's also possible to pass a file-like object. The payload with
            all the docker images is a single zip file.
        docker_images_to_transfer: The list of docker images to transfer. Do not include
            the registry name in the image name.
        docker_images_already_transferred: The list of docker images that have already
            been transferred to the air-gapped registry. Do not include the registry
            name in the image name.
        registry: the registry to push to. It defaults to `registry-1.docker.io` (dockerhub).
        secure: Set to `False` if the registry doesn't support HTTPS (TLS). Default
            is `True`.
        platform: In case of multi platform images, you can precise which one you want to pull.
        username: The username to use for authentication to the registry. Optional if
            the registry doesn't require authentication.
        password: The password to use for authentication to the registry. Optional if
            the registry doesn't require authentication.
    """
    if docker_images_already_transferred is None:
        docker_images_already_transferred = []

    authenticator = Authenticator(username, password)

    with DXFBase(host=registry, auth=authenticator.auth, insecure=not secure) as dxf_base:
        with safezip.ZipFile(zip_file, "w") as zip_file_opened:
            create_zip_from_docker_images(
                dxf_base,
                docker_images_to_transfer,
                docker_images_already_transferred,
                zip_file_opened,
                platform=platform,
            )
