import os
import logging
from typing import Dict
from substrapp.compute_tasks.categories import TASK_CATEGORY_TESTTUPLE
from substrapp.compute_tasks.compute_pod import ComputePod
from substrapp.compute_tasks.directories import AssetBufferDirName, Directories
from substrapp.ledger.api import get_object_from_ledger
from django.conf import settings

logger = logging.getLogger(__name__)


class Context:
    """
    Context represents the execution context of a compute task.

    It is read-only, and scoped to a single compute task. It contains all the context data which is useful during the
    whole lifetime of a compute task: channel name, task key, category, compute plan key, etc...
    """

    _channel_name: str = None
    _task = None
    _task_category = None
    _task_key: str = None
    _compute_plan_key: str = None
    _compute_plan_tag = None
    _directories: Directories = None
    _attempt: int = None  # The attempt number, eg; the number of retries + 1

    def __init__(
        self,
        channel_name: str,
        task: Dict,
        task_category: str,
        task_key: str,
        compute_plan_key: str,
        compute_plan_tag: str,
        directories: Directories,
        attempt: int,
    ):
        self._channel_name = channel_name
        self._task = task
        self._task_category = task_category
        self._task_key = task_key
        self._compute_plan_key = compute_plan_key
        self._compute_plan_tag = compute_plan_tag
        self._directories = directories
        self._attempt = attempt

    @classmethod
    def from_task(cls, channel_name: str, task: Dict, task_category: str, attempt: int):
        task_key = task["key"]
        compute_plan_key = None
        compute_plan_tag = None
        compute_plan_key = task.get("compute_plan_key")
        if compute_plan_key:
            compute_plan = get_object_from_ledger(channel_name, compute_plan_key, "queryComputePlan")
            compute_plan_tag = compute_plan["tag"]

        # TODO orchestrator: this property can be replaced with compute_plan_key once we integrate with orchestrator
        compute_plan_key_safe = compute_plan_key or task_key
        directories = Directories(compute_plan_key_safe)

        return cls(
            channel_name, task, task_category, task_key, compute_plan_key, compute_plan_tag, directories, attempt
        )

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def task(self) -> None:
        return self._task

    @property
    def task_category(self) -> None:
        return self._task_category

    @property
    def task_key(self) -> str:
        return self._task_key

    @property
    def compute_plan_key(self) -> str:
        return self._compute_plan_key

    @property
    def compute_plan_tag(self) -> None:
        return self._compute_plan_tag

    @property
    def directories(self) -> Directories:
        return self._directories

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def compute_plan_key_safe(self):
        # TODO orchestrator: delete this property
        return self.compute_plan_key or self.task_key

    @property
    def algo_key(self):
        return self.task["algo"]["key"]

    @property
    def objective_key(self):
        if self.task_category != TASK_CATEGORY_TESTTUPLE:
            raise Exception(f"Invalid operation: objective_key for {self.task_category}")
        return self.task["objective"]["key"]

    @property
    def algo_image_tag(self):
        return get_algo_image_tag(
            self.task["algo"]["checksum"] if settings.DEBUG_QUICK_IMAGE else self.task["algo"]["key"]
        )

    @property
    def metrics_image_tag(self):
        if self.task_category != TASK_CATEGORY_TESTTUPLE:
            raise Exception(f"Invalid operation: metrics_docker_tag for {self.task_category}")
        slug = (
            self.task["objective"]["metrics"]["checksum"]
            if settings.DEBUG_QUICK_IMAGE
            else self.task["objective"]["key"]
        )
        return f"metrics-{slug[0:8]}".lower()

    @property
    def algo_docker_context_dir(self):
        return os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Algos, self.algo_key)

    @property
    def metrics_docker_context_dir(self):
        return os.path.join(settings.ASSET_BUFFER_DIR, AssetBufferDirName.Metrics, self.objective_key)

    def get_compute_pod(self, is_testtuple_eval: bool) -> ComputePod:
        return ComputePod(self.compute_plan_key_safe, self.algo_key, self.objective_key if is_testtuple_eval else None)


def get_algo_image_tag(algo_key):
    # tag must be lowercase for docker
    return f"algo-{algo_key[0:8]}".lower()
