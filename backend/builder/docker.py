from substrapp.docker_registry import ImageNotFoundError
from substrapp.docker_registry import get_container_manifest


def container_image_exists(image_name: str) -> bool:
    try:
        get_container_manifest(image_name)
    except ImageNotFoundError:
        return False
    else:
        return True
