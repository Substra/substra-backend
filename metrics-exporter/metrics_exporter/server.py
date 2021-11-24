import logging
import structlog
import celery
import prometheus_client
from metrics_exporter import settings, exporter

# Logger configuration
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.LOG_LEVEL)
    )
)
logger = structlog.get_logger()


if __name__ == "__main__":
    metrics_exporter = exporter.Exporter()
    metrics_exporter.register_multiprocess_collector(settings.PROMETHEUS_MULTIPROC_DIR)
    if settings.CELERY_MONITORING_ENABLED:
        app = celery.Celery(broker=settings.CELERY_BROKER_URL)
        metrics_exporter.register_celery_collector(app)
    logger.info("Starting metrics server", port=settings.PORT)
    prometheus_client.start_http_server(settings.PORT, registry=metrics_exporter.registry)
    metrics_exporter.wait()
