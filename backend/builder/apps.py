import kubernetes
from django.apps import AppConfig
from django.conf import settings

from builder.kubernetes import create_replace_private_ca_secret


class BuilderConfig(AppConfig):
    name = "builder"

    def ready(self):
        if settings.TASK["PRIVATE_CA_ENABLED"]:
            kubernetes.config.load_incluster_config()
            k8s_client = kubernetes.client.CoreV1Api()
            create_replace_private_ca_secret(k8s_client)
