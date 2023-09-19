import os

from django.conf import settings


def get_docker_cache_pvc_name() -> str:
    return f"{settings.WORKER_PVC_DOCKER_CACHE}-{os.getenv('HOSTNAME')}"
