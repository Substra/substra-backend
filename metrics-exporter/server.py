import logging
import structlog
from prometheus_client import start_http_server
from settings import PROMETHEUS_MULTIPROC_DIR, PORT, LOG_LEVEL
from exporter import Exporter

# Logger configuration
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(LOG_LEVEL))
)
logger = structlog.get_logger()

if __name__ == "__main__":
    metrics_exporter = Exporter()
    metrics_exporter.register_multiprocess_collector(PROMETHEUS_MULTIPROC_DIR)
    logger.info("Starting metrics server", port=PORT)
    start_http_server(PORT, registry=metrics_exporter.registry)
    metrics_exporter.wait()
