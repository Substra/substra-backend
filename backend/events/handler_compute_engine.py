import typing

from django.conf import settings

import orchestrator
from substrapp.tasks.tasks_outputs import queue_disable_transient_outputs
from substrapp.tasks.tasks_remove_intermediary_models import queue_remove_intermediary_models_from_buffer
from substrapp.tasks.tasks_remove_intermediary_models import queue_remove_intermediary_models_from_db_new

_MY_ORGANIZATION: str = settings.LEDGER_MSP_ID


def _filter_parent_task_outputs_refs(
    task_inputs: typing.Iterable[orchestrator.ComputeTaskInput],
) -> typing.Generator[orchestrator.ComputeTaskInput, None, None]:
    for task_input in task_inputs:
        if task_input.parent_task_key is not None:
            yield task_input


def _map_producer_to_input(
    orc_client: orchestrator.Client, task_inputs: typing.Iterable[orchestrator.ComputeTaskInput]
) -> typing.Generator[tuple[str, orchestrator.ComputeTask], None, None]:
    for task_input in task_inputs:
        if task_input.parent_task_key is None or task_input.parent_task_output_identifier is None:
            raise TypeError("task input is not an output from another task")
        yield (task_input.parent_task_output_identifier, orc_client.query_task(task_input.parent_task_key))


def _filter_outputs_generated_by_worker(
    task_input_producer_mapping: typing.Iterable[tuple[str, orchestrator.ComputeTask]],
    worker: str,
) -> typing.Generator[tuple[str, orchestrator.ComputeTask], None, None]:
    for output_identifer, task in task_input_producer_mapping:
        if task.worker == worker:
            yield (output_identifer, task)


def _filter_transient_outputs(
    task_outputs: typing.Iterable[tuple[str, orchestrator.ComputeTask]],
) -> typing.Generator[tuple[str, str], None, None]:
    for identifier, task in task_outputs:
        if task.outputs[identifier].transient:
            yield identifier, task.key


def _get_deletable_task_outputs(
    orc_client: orchestrator.Client, task_inputs: typing.Iterable[orchestrator.ComputeTaskInput]
) -> list[tuple[str, str]]:
    parent_task_outputs_refs = _filter_parent_task_outputs_refs(task_inputs)
    task_inputs_task_mapping = _map_producer_to_input(orc_client, parent_task_outputs_refs)
    my_task_inputs_task_mapping = _filter_outputs_generated_by_worker(task_inputs_task_mapping, _MY_ORGANIZATION)
    transient_task_outputs = _filter_transient_outputs(my_task_inputs_task_mapping)
    return list(transient_task_outputs)


def _handle_task_outputs(
    orc_client: orchestrator.Client, channel_name: str, task_inputs: typing.Iterable[orchestrator.ComputeTaskInput]
) -> None:
    deletable_outputs = _get_deletable_task_outputs(orc_client, task_inputs)
    queue_disable_transient_outputs(channel_name, deletable_outputs)


def handle_finished_tasks(orc_client: orchestrator.Client, channel_name: str, task: orchestrator.ComputeTask) -> None:
    _handle_task_outputs(orc_client, channel_name, task.inputs)


def handle_disabled_model(channel_name: str, model: orchestrator.Model) -> None:
    queue_remove_intermediary_models_from_buffer(model.key)
    if model.owner == _MY_ORGANIZATION:
        queue_remove_intermediary_models_from_db_new(channel_name, model.key)
