from django.apps import AppConfig
from django.db.models.signals import post_delete


class SubstrappConfig(AppConfig):
    name = 'substrapp'

    def ready(self):
        from .signals.algo.post_delete import algo_post_delete
        from .signals.metric.post_delete import metric_post_delete
        from .signals.datamanager.post_delete import datamanager_post_delete
        from .signals.model.post_delete import model_post_delete

        # registering signals with the model's string label
        from substrapp.models import Algo, Metric, DataManager, Model
        post_delete.connect(algo_post_delete, sender=Algo)
        post_delete.connect(metric_post_delete, sender=Metric)
        post_delete.connect(datamanager_post_delete, sender=DataManager)
        post_delete.connect(model_post_delete, sender=Model)
