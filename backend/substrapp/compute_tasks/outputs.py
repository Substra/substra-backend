import json
import os

import structlog

import orchestrator.computetask_pb2 as computetask_pb2
from orchestrator.client import OrchestratorClient
from substrapp.compute_tasks import command
from substrapp.compute_tasks import directories
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.save_models import save_models
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def save_outputs(ctx: Context) -> None:
    """Saves the outputs from a task

    Args:
        ctx: A task context.
    """
    if ctx.task_category == computetask_pb2.TASK_TEST:
        _save_test_task_outputs(ctx)
    else:
        _save_training_task_outputs(ctx)


def _save_training_task_outputs(ctx: Context) -> None:
    """Saves outputs from a training task

    Args:
        ctx: A task context.
    """
    logger.info("saving models and local folder")
    save_models(ctx)
    directories.commit_dir(ctx.directories, directories.TaskDirName.Local, directories.CPDirName.Local)
    if ctx.has_chainkeys:
        directories.commit_dir(ctx.directories, directories.TaskDirName.Chainkeys, directories.CPDirName.Chainkeys)


def _save_test_task_outputs(ctx: Context) -> None:
    """Saves outputs from a test task on the orchestrator

    Args:
        ctx: A task context.
    """
    logger.info("saving performances")
    with get_orchestrator_client(ctx.channel_name) as client:
        for metric in ctx.metrics:
            perf = _get_perf(ctx.directories, metric.key)
            _register_perf(client, ctx.task_key, metric.key, perf)


def _register_perf(client: OrchestratorClient, task_key: str, metric_key: str, perf: float) -> None:
    """Registers the performance on the orchestrator

    Args:
        client: An open orchestrator client.
        task_key: The key of the compute task that produced this performances.
        metric_key: The key of the metric that produced this performance.
        perf: The performance value.
    """
    performance_obj = {"compute_task_key": task_key, "metric_key": metric_key, "performance_value": perf}
    client.register_performance(performance_obj)


def _get_perf(dirs: directories.Directories, metric_key: str) -> float:
    """Retrieves the performance from the performance file produced by the task

    Args:
        dirs: The compute task directories that contains the task outputs.
        metric_key: The key of the metric from which we want to retrieve the performance.

    Returns:
        The performance as a floating point value.
    """
    perf_path = os.path.join(dirs.task_dir, directories.TaskDirName.Perf, command.get_performance_filename(metric_key))
    with open(perf_path, "r") as perf_file:
        perf = json.load(perf_file)["all"]
        return float(perf)
