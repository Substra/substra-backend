from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import IO
from typing import Dict
from typing import Iterator
from typing import Optional
from typing import Union

import requests
from django.conf import settings
from dxf import DXF
from dxf import DXFBase
from pydantic import BaseModel

from image_transfer.exceptions import ManifestContentError


class PayloadSide(Enum):
    ENCODER = "ENCODER"
    DECODER = "DECODER"


class Blob:
    def __init__(self, dxf_base: DXFBase, digest: str, repository: str):
        self.dxf_base = dxf_base
        self.digest = digest
        self.repository = repository

    def __repr__(self):
        return f"{self.repository}/{self.digest}"

    def __eq__(self, other: Blob):
        return self.digest == other.digest and self.repository == other.repository


class Manifest:
    def __init__(
        self,
        dxf_base: DXFBase,
        docker_image_name: str,
        payload_side: PayloadSide,
        platform: Optional[str] = None,
        content: Optional[str] = None,
    ):
        self.dxf_base = dxf_base
        self.docker_image_name = docker_image_name
        self.payload_side = payload_side
        self.platform = platform
        self._content = content

    @property
    def repository(self) -> str:
        return get_repo_and_tag(self.docker_image_name)[0]

    @property
    def tag(self) -> str:
        return get_repo_and_tag(self.docker_image_name)[1]

    @property
    def content(self) -> str:
        if self._content is None:
            if self.payload_side == PayloadSide.DECODER:
                raise ValueError(
                    "This makes no sense to fetch the manifest from " "the registry if you're decoding the zip"
                )
            dxf = DXF.from_base(self.dxf_base, self.repository)
            self._content = dxf.get_manifest(self.tag, platform=self.platform)
        return self._content

    def get_list_of_blobs(self) -> list[Blob]:
        try:
            manifest_dict = json.loads(self.content)
        except TypeError:
            raise ManifestContentError(
                "The Manifest content must be str, bytes or bytearray. "
                "Is there several platform available in the manifest ? "
                "If yes, please specify it."
            )
        result: list[Blob] = [Blob(self.dxf_base, manifest_dict["config"]["digest"], self.repository)]
        for layer in manifest_dict["layers"]:
            result.append(Blob(self.dxf_base, layer["digest"], self.repository))
        return result


class BlobPathInZip(BaseModel):
    zip_path: str


class BlobLocationInRegistry(BaseModel):
    repository: str


class PayloadDescriptor(BaseModel):
    manifests_paths: Dict[str, Optional[str]]
    blobs_paths: Dict[str, Union[BlobPathInZip, BlobLocationInRegistry]]

    @classmethod
    def from_images(
        cls,
        docker_images_to_transfer: list[str],
        docker_images_already_transferred: list[str],
    ) -> PayloadDescriptor:
        manifests_paths = {}
        for docker_image in docker_images_to_transfer:
            if docker_image in docker_images_already_transferred:
                print(f"Skipping {docker_image} as it has already been transferred")
                manifests_paths[docker_image] = None
            else:
                manifests_paths[docker_image] = f"manifests/{normalize_name(docker_image)}"
        return cls(manifests_paths=manifests_paths, blobs_paths={})

    def get_images_not_transferred_yet(self) -> Iterator[str]:
        for docker_image, manifest_path in self.manifests_paths.items():
            if manifest_path is not None:
                yield docker_image


def normalize_name(docker_image: str) -> str:
    return docker_image.replace("/", "_")


def progress_as_string(index: int, container: list) -> str:
    return f"[{index+1}/{len(container)}]"


def file_to_generator(file_like: IO) -> Iterator[bytes]:
    while True:
        chunk = file_like.read(2**15)
        if not chunk:
            break
        yield chunk


def get_repo_and_tag(docker_image_name: str) -> (str, str):
    return docker_image_name.split(":", 1)


class Authenticator:
    def __init__(self):
        config_path = Path("/.docker/config.json")
        if config_path.is_file():
            with config_path.open("r") as f:
                content = json.load(f)
                self.auth_content = content.get("auths", {}).get(f"{settings.REGISTRY}")

    def auth(self, dxf: DXFBase, response: requests.Response) -> Optional[str]:
        if self.auth_content:
            return dxf.authenticate(
                username=self.auth_content.get("username"),
                password=self.auth_content.get("password"),
                authorization=self.auth_content.get("auth"),
                response=response,
            )

        return None
