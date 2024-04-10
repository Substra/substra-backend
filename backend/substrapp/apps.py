import kubernetes

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_delete

from substrapp.kubernetes_utils import create_replace_private_ca_secret


class SubstrappConfig(AppConfig):
    name = "substrapp"

    def ready(self):
        # registering signals with the model's string label
        from substrapp.models import DataManager
        from substrapp.models import Function
        from substrapp.models import Model

        from .signals.datamanager.post_delete import datamanager_post_delete
        from .signals.function.post_delete import function_post_delete
        from .signals.model.post_delete import model_post_delete

        post_delete.connect(function_post_delete, sender=Function)
        post_delete.connect(datamanager_post_delete, sender=DataManager)
        post_delete.connect(model_post_delete, sender=Model)

        if settings.TASK["PRIVATE_CA_ENABLED"]:
            kubernetes.config.load_incluster_config()
            k8s_client = kubernetes.client.CoreV1Api()
            create_replace_private_ca_secret(k8s_client)
