import typing

import structlog

import orchestrator
from backend.celery import app
from substrapp.orchestrator import get_orchestrator_client

OutputIdentifier = str
TaskKey = str

logger = structlog.get_logger(__name__)


def queue_disable_transient_outputs(channel_name: str, task_outputs: list[tuple[OutputIdentifier, TaskKey]]) -> None:
    from substrapp.task_routing import get_generic_worker_queue

    worker_queue = get_generic_worker_queue()
    remove_transient_outputs_from_orc.apply_async((channel_name, task_outputs), queue=worker_queue)


@app.task(ignore_result=False)
def remove_transient_outputs_from_orc(channel_name: str, task_outputs: list[tuple[OutputIdentifier, TaskKey]]) -> None:
    with get_orchestrator_client(channel_name) as orc_client:
        _remove_transient_outputs(orc_client, task_outputs)


def _remove_transient_outputs(
    orc_client: orchestrator.Client, task_outputs: typing.Iterable[tuple[OutputIdentifier, TaskKey]]
) -> None:
    for output_identifier, task_key in task_outputs:
        try:
            orc_client.disable_task_output(task_key, output_identifier)
        except orchestrator.OrcError as exc:
            logger.debug("output cannot be deleted", error=exc.details, task_key=task_key, identifier=output_identifier)
