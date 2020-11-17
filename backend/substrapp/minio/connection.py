import logging
from django.conf import settings
from minio import Minio

logger = logging.getLogger(__name__)


def minio_create_bucket():
    try:
        minio_client = get_minio_client()
        if not minio_client.bucket_exists('my-test-bucket'):
            minio_client.make_bucket('my-test-bucket')
    except Exception as e:
        logger.error(f'minio error: {e}')


def get_minio_client(endpoint_url=settings.MINIO_ENDPOINT, secure=False):
    minio_client = Minio(endpoint_url,
                         access_key='myaccesskey',
                         secret_key='mysecretkey',
                         secure=secure)
    logger.info(f'minio: connected to {endpoint_url}')
    return minio_client
