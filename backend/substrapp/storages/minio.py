from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from minio import Minio
from minio.error import S3Error
from django.conf import settings


@deconstructible
class MinioStorage(Storage):
    _client = None
    bucket = None

    def __init__(self, bucket, *args, **kwargs):
        self.bucket = bucket
        return super().__init__(*args, **kwargs)

    @property
    def client(self):
        if not self._client:
            self._client = Minio(
                settings.OBJECTSTORE_URL,
                access_key=settings.OBJECTSTORE_ACCESSKEY,
                secret_key=settings.OBJECTSTORE_SECRETKEY,
                secure=False,
            )
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
        return self._client

    def _open(self, name, mode):
        res = self.client.get_object(self.bucket, name)
        f = ContentFile(res.data)
        return f

    def _save(self, name, content):
        self.client.put_object(self.bucket, name, content.file, content.size)
        return name

    def delete(self, name):
        self.client.remove(self.bucket, name)

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
