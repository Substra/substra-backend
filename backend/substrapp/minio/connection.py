import logging
from django.conf import settings
from minio import Minio

logger = logging.getLogger(__name__)


def minio_test():
    try:
        # connect
        minio_client = get_minio_client()

        # create bucket
        if not minio_client.bucket_exists('my-test-bucket'):
            minio_client.make_bucket('my-test-bucket')

        # list buckets
        bucket_list = minio_client.list_buckets()
        for bucket in bucket_list:
            print(bucket.name, bucket)

    except Exception as e:
        logger.error(f'minio error: {e}')


def get_minio_client():
    host = settings.MINIO_ENDPOINT
    minio_client = Minio(host,
                         access_key='myaccesskey',
                         secret_key='mysecretkey',
                         secure=False)
    logger.info(f'minio: connected to {host}')
    return minio_client
