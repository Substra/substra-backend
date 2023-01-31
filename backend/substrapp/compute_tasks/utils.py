import orchestrator


def container_image_tag_from_algo(function: orchestrator.Algo) -> str:
    """builds the container image tag from the function checksum

    Args:
        function (orchestrator.Algo): an function retrieved from the orchestrator

    Returns:
        str: the container image tag
    """
    return f"function-{function.algorithm.checksum[:16]}"
