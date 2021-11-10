import logging
import time
import structlog
from prometheus_client import CollectorRegistry, multiprocess

from settings import LOG_LEVEL

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(LOG_LEVEL))
)
logger = structlog.get_logger()


class Exporter:
    """A prometheus metrics exporter that collect metrics"""

    def __init__(self) -> None:
        logger.info("Creating a metrics exporter")
        self._registry = CollectorRegistry(auto_describe=True)

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

    def wait(self) -> None:
        """wait for metrics infinitely
        """
        while True:
            time.sleep(3600)
