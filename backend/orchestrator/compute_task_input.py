def to_localrep_data(input: dict) -> dict:
    """Convert a compute task input from the orchestrator format to the localrep format"""

    if "parent_task_output" not in input:
        return input

    return {
        "identifier": input["identifier"],
        "parent_task_key": input["parent_task_output"]["parent_task_key"],
        "parent_task_output_identifier": input["parent_task_output"]["output_identifier"],
    }
