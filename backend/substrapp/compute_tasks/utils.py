import orchestrator


def container_image_tag_from_algo(algo: orchestrator.Algo) -> str:
    """builds the container image tag from the algo checksum

    Args:
        algo (orchestrator.Algo): an algo retrieved from the orchestrator

    Returns:
        str: the container image tag
    """
    return f"algo-{algo.algorithm.checksum[:16]}"
