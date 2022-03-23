import time

import structlog
from django.core.management.base import BaseCommand

from events.reactor import consume
from events.reactor import resync

logger = structlog.get_logger("events")


class Command(BaseCommand):
    help = "Consume events from the orchestrator broker"

    def handle(self, *args, **options):
        logger.info("resync local rep")
        # Init: resync all orchestrator assets
        resync()

        logger.debug("starting consume loop")
        # Consume rabbitmq messages indefinitely
        while True:
            try:
                consume()
            except Exception as e:
                logger.exception("Error while consuming messages from the orchestrator RabbitMQ queue, will retry", e=e)
                time.sleep(5)
