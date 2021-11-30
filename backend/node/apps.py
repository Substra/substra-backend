from django.apps import AppConfig
from django.db.models.signals import pre_save


class NodeConfig(AppConfig):
    name = "node"

    def ready(self):
        from node.models import IncomingNode
        from node.signals.node.pre_save import node_pre_save

        pre_save.connect(node_pre_save, sender=IncomingNode)
