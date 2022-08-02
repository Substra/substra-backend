from orchestrator import common_pb2
from orchestrator import computetask_pb2
from substrapp.tests.common import InputIdentifiers


def get_inputs_by_kind(
    task: computetask_pb2.ComputeTask, asset_kind: common_pb2.AssetKind
) -> list[computetask_pb2.ComputeTaskInput]:
    """Get a task's ComputeTaskInputs from an asset kind"""
    return [input for input in task.inputs if task.algo.inputs[input.identifier].kind == asset_kind]


def get_inputs_by_identifier(
    task: computetask_pb2.ComputeTask, identifier: str
) -> list[computetask_pb2.ComputeTaskInput]:
    """Get a task's ComputeTaskInputs from an input identifier"""
    return [input for input in task.inputs if input.identifier == identifier]


def get_data_manager_key(task: computetask_pb2.ComputeTask) -> str:
    """Get a task's data manager key. This will raise if the task has no data manager."""
    return get_inputs_by_identifier(task, InputIdentifiers.OPENER)[0].asset_key


def get_data_sample_keys(task: computetask_pb2.ComputeTask) -> list[str]:
    """Get a task's data sample keys"""
    return [input.asset_key for input in get_inputs_by_identifier(task, InputIdentifiers.DATASAMPLES)]
