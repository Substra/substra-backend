from django.core.files.base import ContentFile as _
from django.core.management.base import BaseCommand

from api.models import Algo
from api.models import ComputePlan
from api.models import ComputeTask
from api.tests import asset_factory as factory


class Command(BaseCommand):
    help = "Generate fixtures"

    def handle(self, *args, **options):
        simple_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_algo_outputs(["model"]),
            category=Algo.Category.ALGO_SIMPLE,
            name="simple algo",
        )
        aggregate_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["model"]),
            outputs=factory.build_algo_outputs(["model"]),
            category=Algo.Category.ALGO_AGGREGATE,
            name="aggregate",
        )
        composite_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "local", "shared"]),
            outputs=factory.build_algo_outputs(["local", "shared"]),
            category=Algo.Category.ALGO_COMPOSITE,
            name="composite",
        )
        metric_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "predictions"]),
            outputs=factory.build_algo_outputs(["performance"]),
            category=Algo.Category.ALGO_METRIC,
            name="metric",
        )

        data_manager = factory.create_datamanager()
        train_data_sample = factory.create_datasample([data_manager])
        test_data_sample = factory.create_datasample([data_manager], test_only=True)

        # CP without task
        factory.create_computeplan(
            name="CP without task",
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
            name="CP with a single todo train task",
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
        train_input_keys = {
            "opener": [data_manager.key],
            "datasamples": [train_data_sample.key],
        }
        factory.create_computetask(
            todo_cp,
            simple_algo,
            inputs=factory.build_computetask_inputs(simple_algo, train_input_keys),
            outputs=factory.build_computetask_outputs(simple_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_TODO,
        )

        # CP with two done train tasks and a doing aggregate train task
        doing_cp = factory.create_computeplan(
            name="CP with two done train tasks and a doing aggregate train task",
            status=ComputePlan.Status.PLAN_STATUS_DOING,
        )
        train_task_1 = factory.create_computetask(
            doing_cp,
            simple_algo,
            inputs=factory.build_computetask_inputs(simple_algo, train_input_keys),
            outputs=factory.build_computetask_outputs(simple_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        model_1 = factory.create_model(train_task_1, identifier="model")
        train_task_2 = factory.create_computetask(
            doing_cp,
            simple_algo,
            inputs=factory.build_computetask_inputs(simple_algo, train_input_keys),
            outputs=factory.build_computetask_outputs(simple_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        model_2 = factory.create_model(train_task_2, identifier="model")
        aggregate_input_keys = {
            "model": [train_task_1.key, train_task_2.key],
        }
        factory.create_computetask(
            doing_cp,
            aggregate_algo,
            inputs=factory.build_computetask_inputs(aggregate_algo, aggregate_input_keys),
            outputs=factory.build_computetask_outputs(aggregate_algo),
            parent_tasks=[train_task_1.key, train_task_2.key],
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DOING,
        )

        # CP with a done train task and a done test task
        done_cp = factory.create_computeplan(
            name="CP with a done train task and a done test task",
            status=ComputePlan.Status.PLAN_STATUS_DONE,
        )
        train_task = factory.create_computetask(
            done_cp,
            simple_algo,
            inputs=factory.build_computetask_inputs(simple_algo, train_input_keys),
            outputs=factory.build_computetask_outputs(simple_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_DONE,
        )
        model_3 = factory.create_model(train_task, identifier="model")
        test_input_keys = {
            "opener": [data_manager.key],
            "datasamples": [test_data_sample.key],
        }
        test_task = factory.create_computetask(
            done_cp,
            metric_algo,
            inputs=factory.build_computetask_inputs(metric_algo, test_input_keys),
            outputs=factory.build_computetask_outputs(metric_algo),
            parent_tasks=[train_task.key],
            data_manager=data_manager,
            data_samples=[test_data_sample.key],
            category=ComputeTask.Category.TASK_TEST,
            status=ComputeTask.Status.STATUS_DONE,
        )
        factory.create_performance(test_task, metric_algo)

        # CP with a done composite train task and a failed test task
        failed_cp = factory.create_computeplan(
            name="CP with a done composite train task and a failed test task",
            status=ComputePlan.Status.PLAN_STATUS_FAILED,
        )
        composite_input_keys = {
            "opener": [data_manager.key],
            "datasamples": [train_data_sample.key],
        }
        composite_task = factory.create_computetask(
            failed_cp,
            composite_algo,
            inputs=factory.build_computetask_inputs(composite_algo, composite_input_keys),
            outputs=factory.build_computetask_outputs(composite_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_COMPOSITE,
            status=ComputeTask.Status.STATUS_DONE,
        )
        model_4 = factory.create_model(composite_task, identifier="local")
        failed_task = factory.create_computetask(
            failed_cp,
            metric_algo,
            inputs=factory.build_computetask_inputs(metric_algo, test_input_keys),
            outputs=factory.build_computetask_outputs(metric_algo),
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
        canceled_cp = factory.create_computeplan(
            name="CP with a single canceled train task",
            status=ComputePlan.Status.PLAN_STATUS_CANCELED,
        )
        factory.create_computetask(
            canceled_cp,
            simple_algo,
            inputs=factory.build_computetask_inputs(simple_algo, train_input_keys),
            outputs=factory.build_computetask_outputs(simple_algo),
            data_manager=data_manager,
            data_samples=[train_data_sample.key],
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_CANCELED,
        )

        # Create files
        factory.create_algo_files(key=simple_algo.key, description=_("Simple Algo"))
        factory.create_algo_files(key=aggregate_algo.key, description=_("Aggregate Algo"))
        factory.create_algo_files(key=composite_algo.key, description=_("Composite Algo"))
        factory.create_algo_files(key=metric_algo.key, description=_("Metric Algo"))
        factory.create_datamanager_files(key=data_manager.key)
        factory.create_datasample_files(key=train_data_sample.key)
        factory.create_datasample_files(key=test_data_sample.key)
        factory.create_model_files(key=model_1.key)
        factory.create_model_files(key=model_2.key)
        factory.create_model_files(key=model_3.key)
        factory.create_model_files(key=model_4.key)
        factory.create_computetask_logs(compute_task_key=failed_task.key)
