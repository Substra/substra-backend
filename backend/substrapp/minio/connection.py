import logging
from django.conf import settings
from minio import Minio

logger = logging.getLogger(__name__)


def get_minio_client(endpoint_url=settings.MINIO_ENDPOINT, secure=False):
    minio_client = Minio(endpoint_url,
                         access_key='myaccesskey',
                         secret_key='mysecretkey',
                         secure=secure)
    logger.info(f'minio: connected to {endpoint_url}')
    return minio_client
