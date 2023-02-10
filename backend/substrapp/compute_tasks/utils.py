import orchestrator


def container_image_tag_from_function(function: orchestrator.Function) -> str:
    """builds the container image tag from the function checksum

    Args:
        function (orchestrator.Function): an function retrieved from the orchestrator

    Returns:
        str: the container image tag
    """
    return f"function-{function.function_address.checksum[:16]}"
