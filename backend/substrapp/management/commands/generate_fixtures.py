from django.core.management.base import BaseCommand

from localrep.models import Algo
from localrep.models import ComputePlan
from localrep.models import ComputeTask
from localrep.models import Model
from substrapp.tests import factory


class Command(BaseCommand):
    help = "Generate fixtures"

    def handle(self, *args, **options):
        simple_algo = factory.create_algo(category=Algo.Category.ALGO_SIMPLE)
        aggregate_algo = factory.create_algo(category=Algo.Category.ALGO_AGGREGATE)
        composite_algo = factory.create_algo(category=Algo.Category.ALGO_COMPOSITE)
        metric_algo = factory.create_algo(category=Algo.Category.ALGO_METRIC)

        data_manager = factory.create_datamanager()
        train_data_sample = factory.create_datasample([data_manager])
        test_data_sample = factory.create_datasample([data_manager], test_only=True)

        # CP without task
        factory.create_computeplan(
            status=ComputePlan.Status.PLAN_STATUS_EMPTY,
            metadata={
                "device": "cpu",
                "epochs": "30",
                "lr_steps": "2 10",
                "optimizer": "Adam",
                "dataset_name": "reg_phase1_new",
            },
        )

        # CP with a single todo train task
        todo_cp = factory.create_computeplan(
            status=ComputePlan.Status.PLAN_STATUS_TODO,
            metadata={
                "device": "cpu",
                "epochs": "50",
                "lr_steps": "2 5",
                "optimizer": "Adam",
                "dataset_name": "hyb_phase1",
                "dropouts_reg": "0.6",
                "regression_weight": "0.75",
            },
        )
        factory.create_computetask(
            todo_cp,
            simple_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_TODO,
        )

        # CP with two done train tasks and a doing aggregate train task
        doing_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DOING)
        train_task_1 = factory.create_computetask(
            doing_cp,
            simple_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_model(train_task_1, category=Model.Category.MODEL_SIMPLE)
        train_task_2 = factory.create_computetask(
            doing_cp,
            simple_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_model(train_task_2, category=Model.Category.MODEL_SIMPLE)
        factory.create_computetask(
            doing_cp,
            aggregate_algo,
            parent_tasks=[train_task_1.key, train_task_2.key],
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DOING,
        )

        # CP with a done train task and a done test task
        done_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_DONE)
        train_task = factory.create_computetask(
            done_cp,
            simple_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_model(train_task, category=Model.Category.MODEL_SIMPLE)
        test_task = factory.create_computetask(
            done_cp,
            metric_algo,
            parent_tasks=[train_task.key],
            data_manager=data_manager,
            data_samples=[test_data_sample.key],
            category=ComputeTask.Category.TASK_TEST,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_performance(test_task, metric_algo)

        # CP with a done composite train task and a failed test task
        failed_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_FAILED)
        composite_task = factory.create_computetask(
            failed_cp,
            composite_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_model(composite_task, category=Model.Category.MODEL_HEAD)
        failed_task = factory.create_computetask(
            failed_cp,
            metric_algo,
            parent_tasks=[composite_task.key],
            data_manager=data_manager,
            data_samples=[test_data_sample.key],
            category=ComputeTask.Category.TASK_TEST,
            status=ComputeTask.Status.STATUS_FAILED,
        )
        failed_cp.failed_task_key = str(failed_task.key)
        failed_cp.failed_task_category = failed_task.category
        failed_cp.save()

        # CP with a single canceled train task
        canceled_cp = factory.create_computeplan(status=ComputePlan.Status.PLAN_STATUS_CANCELED)
        factory.create_computetask(
            canceled_cp,
            simple_algo,
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_CANCELED,
        )
