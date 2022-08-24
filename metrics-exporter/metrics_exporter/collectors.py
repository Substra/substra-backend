import enum
import logging
from typing import Callable

import structlog
from celery.events import state as celery_state
from prometheus_client import metrics
from prometheus_client import metrics_core

from metrics_exporter import settings

State = celery_state.State

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.LOG_LEVEL)))
logger = structlog.get_logger()


class MetricsNames(enum.Enum):
    """An enum of metrics names used in CeleryCollector"""

    CELERY_WORKER_UP = enum.auto()
    CELERY_TASKS_ACTIVE = enum.auto()
    CELERY_TASKS_RECEIVED = enum.auto()
    CELERY_TASKS_STARTED = enum.auto()
    CELERY_TASKS_FAILED = enum.auto()
    CELERY_TASKS_RETRIED = enum.auto()
    CELERY_TASKS_SUCCEEDED = enum.auto()


EVENT_TO_METRIC = {
    "task-received": MetricsNames.CELERY_TASKS_RECEIVED,
    "task-started": MetricsNames.CELERY_TASKS_STARTED,
    "task-failed": MetricsNames.CELERY_TASKS_FAILED,
    "task-retried": MetricsNames.CELERY_TASKS_RETRIED,
    "task-succeeded": MetricsNames.CELERY_TASKS_SUCCEEDED,
}


class CeleryCollector:
    """Collector for Celery metrics
    It is built around the celery state to keep track of tasks progress.
    Celery event handlers should be registered on the celery app.
    """

    def __init__(self, registry, state: State) -> None:

        self._metrics = {}

        self._metrics[MetricsNames.CELERY_WORKER_UP] = metrics.Gauge(
            "celery_worker_up",
            "Indicates if a worker has recently sent a heartbeat",
            ["hostname"],
        )

        self._metrics[MetricsNames.CELERY_TASKS_ACTIVE] = metrics.Gauge(
            "celery_tasks_active", "Number of active tasks on the worker", ["hostname"]
        )

        self._metrics[MetricsNames.CELERY_TASKS_RECEIVED] = metrics.Counter(
            "celery_tasks_received", "Number of Celery tasks received", ["hostname", "name"]
        )

        self._metrics[MetricsNames.CELERY_TASKS_STARTED] = metrics.Counter(
            "celery_tasks_started", "Number of Celery tasks started", ["hostname", "name"]
        )

        self._metrics[MetricsNames.CELERY_TASKS_FAILED] = metrics.Counter(
            "celery_tasks_failed", "Number of Celery tasks that failed to execute", ["hostname", "name"]
        )

        self._metrics[MetricsNames.CELERY_TASKS_RETRIED] = metrics.Counter(
            "celery_tasks_retried", "Number of celery tasks that retried", ["hostname", "name"]
        )

        self._metrics[MetricsNames.CELERY_TASKS_SUCCEEDED] = metrics.Counter(
            "celery_tasks_succeeded", "Number of celery tasks executed successfully", ["hostname", "name"]
        )

        self._celery_state = state

        if registry:
            registry.register(self)

    def heartbeat_handler(self, event) -> None:
        """Process worker-heartbeat events to set metrics

        Args:
            event (Any): the heartbeat event
        """
        worker = self._celery_state.event(event)[0][0]
        logger.debug(
            "Received event",
            alive=worker.alive,
            hostname=worker.hostname,
            active=worker.active,
        )
        self._metrics[MetricsNames.CELERY_WORKER_UP].labels(worker.hostname).set(1 if worker.alive else 0)
        # Here worker.active can be None for the first heartbeat
        self._metrics[MetricsNames.CELERY_TASKS_ACTIVE].labels(worker.hostname).set(worker.active or 0)

    def task_event_handler(self, event) -> None:
        self._celery_state.event(event)
        _task = self._celery_state.tasks.get(event["uuid"])
        if _task:
            task: celery_state.Task = _task
        else:
            return
        if task.worker:
            worker: celery_state.Worker = task.worker
        else:
            return
        logger.debug("received a task event", event_type=event["type"], task=task.as_dict())

        self._metrics[EVENT_TO_METRIC[event["type"]]].labels(worker.hostname, task.name).inc(1)

    @property
    def handlers(self) -> dict[str, Callable]:
        """returns a dict of Celery events handlers

        These handlers should be registered on the celery app through an event reciever.
        celery docs: https://docs.celeryproject.org/en/v5.2.0/userguide/monitoring.html#real-time-processing

        Returns:
            dict[str, Callable]: a dict of event handlers
        """
        handlers = {key: self.task_event_handler for key in EVENT_TO_METRIC.keys()}
        handlers["*"] = self._celery_state.event
        handlers["worker-heartbeat"] = self.heartbeat_handler
        return handlers

    def collect(self) -> list[metrics_core.Metric]:
        """Collects all the Celery metrics

        Returns:
            list[metrics_core.Metric]: A list of celery metrics generated by this collector
        """
        aggregated_metrics = []
        for metric in self._metrics.values():
            aggregated_metrics.extend(metric.collect())
        return aggregated_metrics
