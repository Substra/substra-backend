from substrapp.minio.connection import get_minio_client
from substrapp.minio.url import parse_minio_url


def validate_object_exists(url):
    """
    Will throw if either of these conditions is true:
    - the URL is malformed
    - the resource doesn't exist
    - we don't have permission to access the resource
    """
    secure, endpoint_url, bucket_name, object_name = parse_minio_url(url)

    minio_client = get_minio_client(endpoint_url, secure)
    minio_client.stat_object(bucket_name, object_name)

