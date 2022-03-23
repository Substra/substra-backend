from django.core.management.base import BaseCommand

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.model_pb2 as model_pb2
from substrapp.tests import factory


class Command(BaseCommand):
    help = "Generate fixtures"

    def handle(self, *args, **options):
        algo = factory.create_algo(category=algo_pb2.ALGO_SIMPLE)
        data_manager = factory.create_datamanager()
        data_sample = factory.create_datasample([data_manager])
        compute_plan = factory.create_computeplan(status=computeplan_pb2.PLAN_STATUS_DONE)

        train_task = factory.create_computetask(
            compute_plan,
            algo,
            data_manager=data_manager,
            data_samples=[data_sample.key],
            category=computetask_pb2.TASK_TRAIN,
            status=computetask_pb2.STATUS_DONE,
        )
        factory.create_model(train_task, category=model_pb2.MODEL_SIMPLE)

        metric = factory.create_metric()
        test_task = factory.create_computetask(
            compute_plan,
            algo,
            metrics=[metric],
            data_manager=data_manager,
            data_samples=[data_sample.key],
            parent_tasks=[train_task.key],
            category=computetask_pb2.TASK_TEST,
            status=computetask_pb2.STATUS_DONE,
        )
        factory.create_performance(test_task, metric)
