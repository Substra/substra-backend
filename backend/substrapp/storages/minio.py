import io
from typing import Any

import structlog
import urllib3
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from minio import Minio
from minio.error import S3Error

logger = structlog.get_logger(__name__)


class ReadOnlyMinIOFile(File):
    """A Django File object for files stored in MinIO that only supports read mode"""

    name: str
    _mode: str
    _storage: "MinioStorage"
    _file: urllib3.response.HTTPResponse

    def __init__(self, name: str, mode: str, storage: "MinioStorage", **kwargs) -> None:
        """builds a ReadOnlyMinIOFile

        Args:
            name (str): name of the file to open
            mode (str): opening mode for the file, only read modes are supported
            storage (MinioStorage): storage backend used to store this file

        Raises:
            NotImplementedError: raised if a mode different from read is requested
        """
        if "w" in mode:
            raise NotImplementedError("ReadOnlyMinIOFile storage only supports read modes")
        self._storage = storage
        self.name = name
        self._mode = mode
        self._file = None

    def _get_file(self) -> Any:
        """open the file object

        Returns:
            Any: an opened file object
        """
        if self._file is None:
            self._open_file_at(0)
        return self._file

    def _open_file_at(self, offset: int) -> None:
        """open the internal file reference at the required position

        Args:
            offset (int): start byte position of the data
        """
        self._file: urllib3.response.HTTPResponse = self._storage.client.get_object(
            self._storage.bucket, self.name, offset=offset
        )

    def _set_file(self, value):
        """Set the internal file

        Args:
            value (urllib3.response.HTTPResponse): the file you want to set
        """
        self._file = value

    file = property(_get_file, _set_file)

    def close(self) -> None:
        """close the file"""
        if self._file is not None:
            self._file.close()
            self._file.release_conn()
            self._file = None

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Change the stream position to the given byte offset

        Args:
            offset (int): offset at which you want to set the stream position
            whence (int, optional): position from which the offset is computed. Defaults to io.SEEK_SET.
                only io.SEEK_SET is accepted.

        Raises:
            NotImplementedError: raised if whence is set to something else than io.SEEK_SET

        Returns:
            int: the new stream position
        """
        if whence != io.SEEK_SET:
            raise NotImplementedError("This file does not support seek modes other than SEEK_SET")
        # Not ideal but since HTTPResponse does not support seek()
        # we need to reopen the file at the required position
        self.close()
        self._open_file_at(offset)
        return offset

    def writable(self) -> bool:
        """checks if this file is writable

        Returns:
            bool: whether the file is writable or not
        """
        return False

    def write(*args, **kwargs):
        """write to the file

        Raises:
            NotImplementedError: always raised because this file is readonly
        """
        raise NotImplementedError("this is a readonly file")


@deconstructible
class MinioStorage(Storage):
    _client = None
    bucket = None

    def __init__(self, bucket, *args, **kwargs):
        self.bucket = bucket
        super().__init__(*args, **kwargs)

    @property
    def client(self):
        if not self._client:
            client = Minio(
                settings.OBJECTSTORE_URL,
                access_key=settings.OBJECTSTORE_ACCESSKEY,
                secret_key=settings.OBJECTSTORE_SECRETKEY,
                secure=False,
            )
            try:
                client.make_bucket(self.bucket)
            except S3Error as err:
                if err.code != "BucketAlreadyOwnedByYou":
                    raise
            else:
                logger.info("MinIO bucket created", bucket=self.bucket)
            self._client = client
        return self._client

    def _open(self, name, mode):
        return ReadOnlyMinIOFile(name, mode, self)

    def _save(self, name, content):
        self.client.put_object(self.bucket, name, content.file, content.size)
        return name

    def delete(self, name):
        logger.debug("Deleting object from Minio", name=name, bucket=self.bucket)
        self.client.remove_object(self.bucket, name)

    def exists(self, name):
        try:
            self.client.stat_object(self.bucket, name)
        except S3Error as err:
            if err.code == "NoSuchKey":
                return False
            raise err
        else:
            return True

    def url(self, name):
        # django-rest-framework uses this method for serialization.
        # But this url is not used to get access to the object.
        return f"{self.bucket}/{name}"
