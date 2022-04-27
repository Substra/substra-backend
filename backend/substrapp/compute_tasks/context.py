from typing import Any
from typing import Dict
from typing import List

from django.conf import settings

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks.algo import Algo
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.directories import Directories
from substrapp.orchestrator import get_orchestrator_client

TASK_DATA_FIELD = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "test",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
    computetask_pb2.TASK_COMPOSITE: "composite",
}


class Context:
    """
    Context represents the execution context of a compute task.

    It is read-only, and scoped to a single compute task. It contains all the context data which is useful during the
    whole lifetime of a compute task: channel name, task key, category, compute plan key, etc...
    """

    _channel_name: str
    _task: Dict[str, Any]
    _task_category: "computetask_pb2.ComputeTaskCategory.ValueType"
    _task_key: str
    _compute_plan_key: str
    _compute_plan_tag: str
    _compute_plan: Dict
    _in_models: List[Dict]
    _data_manager: Dict
    _directories: Directories
    _algo: Algo
    _metrics: list[Algo]
    _has_chainkeys: bool

    def __init__(
        self,
        channel_name: str,
        task: Dict[str, Any],
        task_category: "computetask_pb2.ComputeTaskCategory.ValueType",
        task_key: str,
        compute_plan: Dict,
        compute_plan_key: str,
        compute_plan_tag: str,
        in_models: List[Dict],
        algo: dict[str, Any],
        metrics: list[dict[str, Any]],
        data_manager: Dict,
        directories: Directories,
        has_chainkeys: bool,
    ):
        self._channel_name = channel_name
        self._task = task
        self._compute_plan = compute_plan
        self._task_category = task_category
        self._task_key = task_key
        self._compute_plan_key = compute_plan_key
        self._compute_plan_tag = compute_plan_tag
        self._in_models = in_models
        self._metrics = [Algo(self._channel_name, metric) for metric in metrics]
        self._data_manager = data_manager
        self._directories = directories
        self._has_chainkeys = has_chainkeys
        self._algo = Algo(self._channel_name, algo)

    @classmethod
    def from_task(cls, channel_name: str, task: Dict):
        task_key = task["key"]
        compute_plan_key = task["compute_plan_key"]
        metrics = []
        data_manager = None

        task_category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
        task_data = task[TASK_DATA_FIELD[task_category]]

        # fetch more information from the orchestrator
        with get_orchestrator_client(channel_name) as client:
            compute_plan = client.query_compute_plan(compute_plan_key)
            in_models = client.get_computetask_input_models(task["key"])
            algo = client.query_algo(task["algo"]["key"])

            if task_category == computetask_pb2.TASK_TEST:
                metrics = [client.query_algo(metric_key) for metric_key in task_data["metric_keys"]]

            if task_category in [computetask_pb2.TASK_COMPOSITE, computetask_pb2.TASK_TRAIN, computetask_pb2.TASK_TEST]:
                data_manager = client.query_datamanager(task_data["data_manager_key"])

        directories = Directories(compute_plan_key)

        compute_plan_tag = compute_plan["tag"]
        cp_is_tagged = True if compute_plan_tag else False
        has_chainkeys = settings.TASK["CHAINKEYS_ENABLED"] and cp_is_tagged

        return cls(
            channel_name,
            task,
            task_category,
            task_key,
            compute_plan,
            compute_plan_key,
            compute_plan_tag,
            in_models,
            algo,
            metrics,
            data_manager,
            directories,
            has_chainkeys,
        )

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def task(self) -> Dict[str, Any]:
        return self._task

    @property
    def task_category(self) -> "computetask_pb2.ComputeTaskCategory.ValueType":
        return self._task_category

    @property
    def task_key(self) -> str:
        return self._task_key

    @property
    def task_rank(self) -> int:
        return self.task["rank"]

    @property
    def compute_plan_key(self) -> str:
        return self._compute_plan_key

    @property
    def compute_plan_tag(self) -> str:
        return self._compute_plan_tag

    @property
    def directories(self) -> Directories:
        return self._directories

    @property
    def has_chainkeys(self) -> bool:
        return self._has_chainkeys

    @property
    def in_models(self) -> List[Dict]:
        return self._in_models

    @property
    def algo(self) -> Algo:
        return self._algo

    @property
    def compute_plan(self) -> Dict:
        return self._compute_plan

    @property
    def metrics(self) -> list[Algo]:
        return self._metrics

    @property
    def data_manager(self) -> Dict:
        return self._data_manager

    @property
    def task_data(self) -> Dict:
        task_data_field = TASK_DATA_FIELD[self.task_category]
        return self.task[task_data_field]

    @property
    def data_sample_keys(self) -> List[str]:
        if self.task_category not in [
            computetask_pb2.TASK_COMPOSITE,
            computetask_pb2.TASK_TRAIN,
            computetask_pb2.TASK_TEST,
        ]:
            return []
        return self.task_data["data_sample_keys"]

    def get_compute_pod(self, algo_key: str) -> ComputePod:
        return ComputePod(self.compute_plan_key, algo_key)

    @property
    def all_algos(self) -> list[Algo]:
        all_algos = [self._algo]
        all_algos.extend(self._metrics)
        return all_algos
