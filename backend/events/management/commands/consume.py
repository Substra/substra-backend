import time

import structlog
from django.core.management.base import BaseCommand

from events import health
from events.reactor import consume

logger = structlog.get_logger("events")


class Command(BaseCommand):
    help = "Consume events from the orchestrator broker"

    def handle(self, *args, **options):
        health_service = health.HealthService()
        logger.debug("starting consume loop")
        # Consume grpc streams indefinitely
        while True:
            try:
                consume(health_service)
            except Exception as e:
                logger.exception("Error while consuming messages from the orchestrator gRPC streams, will retry", e=e)
                time.sleep(5)
