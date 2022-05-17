from django.core.management.base import BaseCommand

from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import Model
from substrapp.tests import factory


class Command(BaseCommand):
    help = "Generate fixtures"

    def handle(self, *args, **options):
        algo = factory.create_algo(category=Algo.Category.ALGO_SIMPLE)
        data_manager = factory.create_datamanager()
        data_sample = factory.create_datasample([data_manager])
        compute_plan = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)

        train_task = factory.create_computetask(
            compute_plan,
            algo,
            data_manager=data_manager,
            data_samples=[data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_model(train_task, category=Model.Category.MODEL_SIMPLE)

        metric = factory.create_metric()
        test_task = factory.create_computetask(
            compute_plan,
            algo,
            metrics=[metric],
            data_manager=data_manager,
            data_samples=[data_sample.key],
            parent_tasks=[train_task.key],
            category=ComputeTask.Category.TASK_TEST,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_performance(test_task, metric)
