import logging
import time
import structlog
from prometheus_client import CollectorRegistry, multiprocess

from metrics_exporter import settings, collectors

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.LOG_LEVEL)
    )
)
logger = structlog.get_logger()


class Exporter:
    """A prometheus metrics exporter that collect metrics"""

    def __init__(self) -> None:
        logger.info("Creating a metrics exporter")
        self._registry = CollectorRegistry(auto_describe=True)
        self._celery_app = None
        self._celery_state = None
        self._celery_collector = None

    @property
    def registry(self) -> CollectorRegistry:
        """the metrics registry that can be exposed

        Returns:
            CollectorRegistry: a prometheus_client CollectorRegistry
        """
        return self._registry

    def register_multiprocess_collector(self, path: str) -> None:
        """registers a multiprocess collector on the exporter

        Args:
        path (str): metrics path on the filesystem
        """
        logger.info("Adding a multiprocess collector", metrics_path=path)
        multiprocess.MultiProcessCollector(self.registry, path)

    def register_celery_collector(self, app) -> None:
        """registers a Celery collector on the exporter

        Args:
            app (Celery): A celery app object
        """
        logger.info("Adding a celery collector")
        self._celery_app = app
        self._celery_state = app.events.State()
        self._celery_collector = collectors.CeleryCollector(
            self.registry, self._celery_state
        )

    def wait(self) -> None:
        """wait for metrics infinitely"""
        if not self._celery_app:
            while True:
                try:
                    time.sleep(3600)
                except KeyboardInterrupt as exc:
                    raise SystemExit from exc
        else:
            conn = self._celery_app.connection_for_read()
            recv = self._celery_app.events.Receiver(
                conn, handlers=self._celery_collector.handlers
            )
            try:
                recv.capture(limit=None)
            except KeyboardInterrupt as exc:
                raise SystemExit from exc
