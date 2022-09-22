import copy

import orchestrator.computetask_pb2 as computetask_pb2


def orc_to_api(data: dict) -> dict:
    """Convert a compute task from the orchestrator format to the api format"""

    res = copy.deepcopy(data)
    res["algo"] = {"key": res.pop("algo_key")}
    res["inputs"] = [_input_to_api(input) for input in res["inputs"]]
    res["outputs"] = [{"identifier": identifier, **output} for identifier, output in res["outputs"].items()]
    return res


def api_to_orc(data: dict) -> dict:
    """Convert a compute task from the api format to the orchestrator format"""

    res = copy.deepcopy(data)
    res["inputs"] = [_get_task_input(input) for input in data["inputs"]]
    res["outputs"] = {
        identifier: computetask_pb2.NewComputeTaskOutput(
            permissions=output["permissions"], transient=output.get("transient")
        )
        for identifier, output in data["outputs"].items()
    }
    algo = res.pop("algo")
    res["algo_key"] = algo["key"]

    return res


def _input_to_api(input: dict) -> dict:
    """Convert a compute task input from the orchestrator format to the api format"""

    if "parent_task_output" not in input:
        return input

    return {
        "identifier": input["identifier"],
        "parent_task_key": input["parent_task_output"]["parent_task_key"],
        "parent_task_output_identifier": input["parent_task_output"]["output_identifier"],
    }


def _get_task_input(self, input: dict) -> computetask_pb2.ComputeTaskInput:
    """Convert a dict into a computetask_pb2.ComputeTaskInput"""

    if input["asset_key"]:
        return computetask_pb2.ComputeTaskInput(
            identifier=input["identifier"],
            asset_key=input["asset_key"],
        )

    return computetask_pb2.ComputeTaskInput(
        identifier=input["identifier"],
        parent_task_output=computetask_pb2.ParentTaskOutputRef(
            parent_task_key=input["parent_task_key"],
            output_identifier=input["parent_task_output_identifier"],
        ),
    )
