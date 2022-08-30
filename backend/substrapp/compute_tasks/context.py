import os
from typing import Optional

import structlog
from django.conf import settings

import orchestrator
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.errors import InvalidContextError
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


class TaskResource(dict):
    """TaskResource represents a task's input or output.

    By inheriting from dict, we get JSON serialization for free
    """

    def __init__(self, id: str, value: str):
        dict.__init__(self, id=id, value=value)


class Context:
    """
    Context represents the execution context of a compute task.

    It is scoped to a single compute task. It contains all the context data which is useful during the
    whole lifetime of a compute task: channel name, task key, category, compute plan key, etc...
    """

    _channel_name: str
    _task: orchestrator.ComputeTask
    _compute_plan: orchestrator.ComputePlan
    _input_assets: list[orchestrator.ComputeTaskInputAsset]
    _directories: Directories
    _algo: orchestrator.Algo
    _has_chainkeys: bool
    _outputs: dict[str, str]

    def __init__(
        self,
        channel_name: str,
        task: orchestrator.ComputeTask,
        compute_plan: orchestrator.ComputePlan,
        input_assets: list[orchestrator.ComputeTaskInputAsset],
        algo: orchestrator.Algo,
        directories: Directories,
        has_chainkeys: bool,
    ):
        self._channel_name = channel_name
        self._task = task
        self._compute_plan = compute_plan
        self._input_assets = input_assets
        self._directories = directories
        self._has_chainkeys = has_chainkeys
        self._algo = algo
        self._outputs = {}

    @classmethod
    def from_task(cls, channel_name: str, task: orchestrator.ComputeTask):
        compute_plan_key = task.compute_plan_key

        # fetch more information from the orchestrator
        with get_orchestrator_client(channel_name) as client:
            compute_plan = client.query_compute_plan(compute_plan_key)
            input_assets = client.get_task_input_assets(task.key)
            algo = client.query_algo(task.algo_key)

        logger.debug("retrieved input assets from orchestrator", input_assets=input_assets)

        directories = Directories(compute_plan_key)

        has_chainkeys = settings.TASK["CHAINKEYS_ENABLED"] and bool(compute_plan.tag)

        return cls(
            channel_name,
            task,
            compute_plan,
            input_assets,
            algo,
            directories,
            has_chainkeys,
        )

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def task(self) -> orchestrator.ComputeTask:
        return self._task

    @property
    def compute_plan_key(self) -> str:
        return self._task.compute_plan_key

    @property
    def directories(self) -> Directories:
        return self._directories

    @property
    def has_chainkeys(self) -> bool:
        return self._has_chainkeys

    @property
    def input_assets(self) -> list[orchestrator.ComputeTaskInputAsset]:
        return self._input_assets

    @property
    def input_models(self) -> list[orchestrator.Model]:
        """Return the models passed as task inputs"""
        return [input.model for input in self._input_assets if input.kind == orchestrator.AssetKind.ASSET_MODEL]

    @property
    def algo(self) -> orchestrator.Algo:
        return self._algo

    @property
    def compute_plan(self) -> orchestrator.ComputePlan:
        return self._compute_plan

    @property
    def data_manager(self) -> Optional[orchestrator.DataManager]:
        dm = [
            input.data_manager
            for input in self._input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_MANAGER
        ]
        if len(dm) > 1:
            raise InvalidContextError("there are too many datamanagers")
        return dm[0] if dm else None

    @property
    def data_sample_keys(self) -> list[str]:
        return [
            input.data_sample.key
            for input in self._input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_SAMPLE
        ]

    def get_compute_pod(self, algo_key: str) -> ComputePod:
        return ComputePod(self.compute_plan_key, algo_key)

    def get_output_identifier(self, value: str) -> str:
        """return the task output identifier from output path"""
        path = os.path.relpath(value, self.directories.task_dir)
        return self._outputs[path]

    def set_outputs(self, outputs: list[TaskResource]):
        """set_outputs should be called with outputs as passed to the algo"""
        for output in outputs:
            path = os.path.relpath(output["value"], SANDBOX_DIR)
            self._outputs[path] = output["id"]
