from urllib.parse import urlparse


def is_minio_url(url):
    try:
        parse_minio_url(url)
        return url.scheme in ['http', 'https']
    except Exception:
        return False


def parse_minio_url(url):
    url_comp = urlparse(url)

    endpoint_url = url_comp.netloc
    secure = url_comp.scheme == 'https'
    bucket_name = url_comp.path[0]
    object_name = '/'.join(url_comp.path.split('/')[1:])

    return secure, endpoint_url, bucket_name, object_name
