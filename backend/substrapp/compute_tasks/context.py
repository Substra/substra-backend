from typing import Any
from typing import Dict
from typing import List

from django.conf import settings

import orchestrator.computetask_pb2 as computetask_pb2
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.directories import Directories
from substrapp.orchestrator import get_orchestrator_client

TASK_DATA_FIELD = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "test",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
    computetask_pb2.TASK_COMPOSITE: "composite",
}

METRICS_IMAGE_PREFIX = "metrics"
ALGO_IMAGE_PREFIX = "algo"


class Context:
    """
    Context represents the execution context of a compute task.

    It is read-only, and scoped to a single compute task. It contains all the context data which is useful during the
    whole lifetime of a compute task: channel name, task key, category, compute plan key, etc...
    """

    _channel_name: str
    _task: Dict[str, Any]
    _task_category: computetask_pb2.ComputeTaskCategory.ValueType
    _task_key: str
    _compute_plan_key: str
    _compute_plan_tag: str
    _compute_plan: Dict
    _in_models: List[Dict]
    _algo: Dict
    _metrics: Dict
    _data_manager: Dict
    _directories: Directories
    _attempt: int  # The attempt number, eg; the number of retries + 1
    _has_chainkeys: bool

    def __init__(
        self,
        channel_name: str,
        task: Dict[str, Any],
        task_category: computetask_pb2.ComputeTaskCategory.ValueType,
        task_key: str,
        compute_plan: Dict,
        compute_plan_key: str,
        compute_plan_tag: str,
        in_models: List[Dict],
        algo: Dict,
        metrics: Dict,
        data_manager: Dict,
        directories: Directories,
        attempt: int,
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
        self._algo = algo
        self._metrics = metrics
        self._data_manager = data_manager
        self._directories = directories
        self._attempt = attempt
        self._has_chainkeys = has_chainkeys

    @classmethod
    def from_task(cls, channel_name: str, task: Dict, attempt: int):
        task_key = task["key"]
        compute_plan_key = task["compute_plan_key"]
        metrics = None
        data_manager = None

        task_category = computetask_pb2.ComputeTaskCategory.Value(task["category"])
        task_data = task[TASK_DATA_FIELD[task_category]]

        # fetch more information from the orchestrator
        with get_orchestrator_client(channel_name) as client:
            compute_plan = client.query_compute_plan(compute_plan_key)
            in_models = client.get_computetask_input_models(task["key"])
            algo = client.query_algo(task["algo"]["key"])

            if task_category == computetask_pb2.TASK_TEST:
                metrics = {metric_key: client.query_algo(metric_key) for metric_key in task_data["metric_keys"]}

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
            attempt,
            has_chainkeys,
        )

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def task(self) -> Dict[str, Any]:
        return self._task

    @property
    def task_category(self) -> computetask_pb2.ComputeTaskCategory.ValueType:
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
    def attempt(self) -> int:
        return self._attempt

    @property
    def has_chainkeys(self) -> bool:
        return self._has_chainkeys

    @property
    def algo_key(self) -> str:
        return self.task["algo"]["key"]

    @property
    def metric_keys(self) -> List[str]:
        if self.task_category != computetask_pb2.TASK_TEST:
            raise Exception(f"Invalid operation: metric_keys for {self.task_category}")
        return self.task_data["metric_keys"]

    @property
    def in_models(self) -> List[Dict]:
        return self._in_models

    @property
    def algo(self) -> Dict:
        return self._algo

    @property
    def compute_plan(self) -> Dict:
        return self._compute_plan

    @property
    def metrics(self) -> Dict:
        return self._metrics

    @property
    def data_manager(self) -> Dict:
        return self._data_manager

    @property
    def algo_image_tag(self) -> str:
        algo_key = self.task["algo"]["key"]
        return get_image_tag(ALGO_IMAGE_PREFIX, algo_key)

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

    @property
    def metrics_image_tags(self) -> Dict[str, str]:
        if self.task_category != computetask_pb2.TASK_TEST:
            raise Exception(f"Invalid operation: metrics_docker_tag for {self.task_category}")

        metric_keys = self.task_data["metric_keys"]

        return {slug: get_image_tag(METRICS_IMAGE_PREFIX, slug) for slug in metric_keys}

    def get_compute_pod(self, is_testtuple_eval: bool, metric_key: str = "") -> ComputePod:
        return ComputePod(self.compute_plan_key, self.algo_key, metric_key if is_testtuple_eval else "")


def get_image_tag(prefix, key) -> str:
    # tag must be lowercase for docker
    return f"{prefix}-{key[0:8]}".lower()
