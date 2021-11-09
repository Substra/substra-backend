import logging
import time
import os
import structlog
from prometheus_client import (CollectorRegistry, multiprocess,
                               start_http_server)

# App settings
PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/")
PORT = int(os.environ.get("PORT", 8001))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Logger configuration
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(LOG_LEVEL))
)
logger = structlog.get_logger()


def create_collector_registry(path: str) -> CollectorRegistry:
    """Builds a CollectorRegistry collecting metrics from a directory

    Args:
        path (str): metrics data path

    Returns:
        CollectorRegistry: The multiprocess collector registry
    """
    logger.info("Creating a metrics collector", metrics_path=path)
    multiproc_registry = CollectorRegistry(auto_describe=True)
    multiprocess.MultiProcessCollector(multiproc_registry, path=path)
    return multiproc_registry


if __name__ == "__main__":
    registry = create_collector_registry(PROMETHEUS_MULTIPROC_DIR)
    logger.info("Starting metrics server", port=PORT)
    start_http_server(PORT, registry=registry)
    # The http server is started in a different thread so we need to wait in the main thread
    while True:
        time.sleep(3600)
