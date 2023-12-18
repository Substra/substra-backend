import multiprocessing
import time

import structlog
from django.apps import AppConfig
from django.conf import settings
from grpc import StatusCode

from orchestrator.error import OrcError
from substrapp.orchestrator import get_orchestrator_client

logger = structlog.get_logger(__name__)


def _register_organization(channel_name: str) -> None:
    structlog.contextvars.bind_contextvars(channel=channel_name)
    # We try until success, if it fails the backend will not start
    while True:
        with get_orchestrator_client(channel_name) as client:
            try:
                client.register_organization({"address": settings.DEFAULT_DOMAIN})
            except OrcError as rpc_error:
                code = rpc_error.code
                if code == StatusCode.ALREADY_EXISTS:
                    break
                time.sleep(1)
                logger.info("Retry registering the organization on the orchestrator", exc_info=rpc_error)
            else:
                logger.info("Organization registered on the orchestrator")
                break


class OrganizationRegisterConfig(AppConfig):
    name = "organization_register"

    def register_organization(self, channel_name: str) -> None:
        proc = multiprocessing.Process(target=_register_organization, args=(channel_name,))
        proc.start()

    def ready(self) -> None:
        if not settings.ISOLATED:
            for channel_name in settings.CHANNELS.keys():
                self.register_organization(channel_name)
