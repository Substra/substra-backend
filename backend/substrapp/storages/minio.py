import tempfile

import structlog
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from minio import Minio
from minio import error as merr
from minio.error import S3Error

logger = structlog.get_logger(__name__)

MINIO_CLIENT_CHUNK_SIZE = 1024 * 1024
SPOOLED_TEMPORARY_FILE_MAX_SIZE = 1024 * 1024 * 10


# From https://github.com/py-pa/django-minio-storage
class ReadOnlySpooledTemporaryFile(File):
    """A django File class which buffers the minio object into a local SpooledTemporaryFile."""

    minio_client_chunk_size = MINIO_CLIENT_CHUNK_SIZE
    max_memory_size = SPOOLED_TEMPORARY_FILE_MAX_SIZE

    def __init__(
        self,
        name: str,
        mode: str,
        storage: "Storage",
        **kwargs,
    ):
        if "w" in mode:
            raise NotImplementedError("ReadOnlySpooledTemporaryFile storage only support read modes")
        self._storage: "Storage" = storage
        self.name: str = name
        self._mode: str = mode
        self._file = None

    def _get_file(self):
        if self._file is None:
            try:
                obj = self._storage.client.get_object(self._storage.bucket, self.name)
                self._file = tempfile.SpooledTemporaryFile(max_size=self.max_memory_size)
                for d in obj.stream(amt=self.minio_client_chunk_size):
                    self._file.write(d)
                self._file.seek(0)
                return self._file
            except merr.ResponseError as error:
                raise Exception(f"File {self.name} does not exist", error)
            finally:
                try:
                    obj.close()
                    obj.release_conn()
                except Exception as e:
                    logger.error(str(e))
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def writable(self) -> bool:
        return False

    def write(*args, **kwargs):
        raise NotImplementedError("this is a read only file")


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
        return ReadOnlySpooledTemporaryFile(name, mode, self)

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
