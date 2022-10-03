import structlog
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from api.models import ComputePlan
from api.models import ComputeTask
from api.tests import asset_factory as factory

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Generate fixtures"

    def handle(self, *args, **options):
        logger.debug("Generate test data")
        self.create_algos()
        self.create_data_manager()
        self.create_data_samples()
        self.create_empty_cp()
        for status in [
            ComputePlan.Status.PLAN_STATUS_TODO,
            ComputePlan.Status.PLAN_STATUS_DOING,
            ComputePlan.Status.PLAN_STATUS_DONE,
            ComputePlan.Status.PLAN_STATUS_FAILED,
            ComputePlan.Status.PLAN_STATUS_CANCELED,
        ]:
            self.create_basic_cp(status)
        self.create_aggregate_cp()
        self.create_composite_cp()

    def create_algos(self):
        logger.debug("  Create algos")
        self.simple_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="simple",
        )
        factory.create_algo_files(
            key=self.simple_algo.key,
            description=ContentFile("Simple algo"),
        )

        self.aggregate_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["models"]),
            outputs=factory.build_algo_outputs(["model"]),
            name="aggregate",
        )
        factory.create_algo_files(
            key=self.aggregate_algo.key,
            description=ContentFile("Aggregate algo"),
        )

        self.composite_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "local", "shared"]),
            outputs=factory.build_algo_outputs(["local", "shared"]),
            name="composite",
        )
        factory.create_algo_files(
            key=self.composite_algo.key,
            description=ContentFile("Composite algo"),
        )

        self.predict_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "model", "shared"]),
            outputs=factory.build_algo_outputs(["predictions"]),
            name="predict",
        )
        factory.create_algo_files(
            key=self.predict_algo.key,
            description=ContentFile("Predict algo"),
        )

        self.metric_algo = factory.create_algo(
            inputs=factory.build_algo_inputs(["datasamples", "opener", "predictions"]),
            outputs=factory.build_algo_outputs(["performance"]),
            name="metric",
        )
        factory.create_algo_files(
            key=self.metric_algo.key,
            description=ContentFile("Metric algo"),
        )

    def create_data_manager(self):
        logger.debug("  Create data manager")
        self.data_manager = factory.create_datamanager()
        factory.create_datamanager_files(key=self.data_manager.key)

    def create_data_samples(self):
        logger.debug("  Create data samples")
        self.train_data_sample_keys = []
        self.predict_data_sample_keys = []
        self.test_data_sample_keys = []

        # arbitrary number in order to have multiple datasamples
        for _ in range(3):
            train_data_sample = factory.create_datasample([self.data_manager])
            factory.create_datasample_files(key=train_data_sample.key)
            self.train_data_sample_keys.append(train_data_sample.key)

            predict_data_sample = factory.create_datasample([self.data_manager])
            factory.create_datasample_files(key=predict_data_sample.key)
            self.predict_data_sample_keys.append(predict_data_sample.key)

            test_data_sample = factory.create_datasample([self.data_manager])
            factory.create_datasample_files(key=test_data_sample.key)
            self.test_data_sample_keys.append(test_data_sample.key)

    def create_empty_cp(self):
        logger.debug("  Create empty CP")
        # no task
        return factory.create_computeplan(
            name="empty",
            status=ComputePlan.Status.PLAN_STATUS_EMPTY,
        )

    def create_basic_cp(self, cp_status):
        logger.debug(f"  Create basic CP [{cp_status}]")
        # train -> predict -> test
        cp = factory.create_computeplan(
            name=f"basic [{cp_status}]",
            status=cp_status,
            metadata={
                "status": cp_status,
            },
        )

        first_task_status = cp_status
        train_task = factory.create_computetask(
            cp,
            self.simple_algo,
            inputs=factory.build_computetask_inputs(
                self.simple_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.train_data_sample_keys,
                },
            ),
            outputs=factory.build_computetask_outputs(self.simple_algo),
            data_manager=self.data_manager,
            data_samples=self.train_data_sample_keys,
            category=ComputeTask.Category.TASK_TRAIN,
            status=first_task_status,
        )
        if first_task_status == ComputeTask.Status.STATUS_DONE:
            model = factory.create_model(
                train_task,
                identifier="model",
            )
            factory.create_model_files(key=model.key)
        elif first_task_status == ComputeTask.Status.STATUS_FAILED:
            factory.create_computetask_logs(compute_task_key=train_task.key)
            cp.failed_task_key = str(train_task.key)
            cp.failed_task_category = train_task.category
            cp.save()

        task_status = (
            ComputeTask.Status.STATUS_DONE
            if cp_status == ComputePlan.Status.PLAN_STATUS_DONE
            else ComputeTask.Status.STATUS_TODO
        )
        predict_task = factory.create_computetask(
            cp,
            self.predict_algo,
            inputs=factory.build_computetask_inputs(
                self.predict_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.predict_data_sample_keys,
                    "model": [train_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(self.predict_algo),
            data_manager=self.data_manager,
            data_samples=self.predict_data_sample_keys,
            category=ComputeTask.Category.TASK_PREDICT,
            status=task_status,
        )
        if task_status == ComputeTask.Status.STATUS_DONE:
            predictions = factory.create_model(
                predict_task,
                identifier="predictions",
            )
            factory.create_model_files(key=predictions.key)

        test_task = factory.create_computetask(
            cp,
            self.metric_algo,
            inputs=factory.build_computetask_inputs(
                self.metric_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.test_data_sample_keys,
                    "predictions": [predict_task.key],
                },
            ),
            outputs=factory.build_computetask_outputs(self.metric_algo),
            data_manager=self.data_manager,
            data_samples=self.test_data_sample_keys,
            category=ComputeTask.Category.TASK_TEST,
            status=task_status,
        )
        if task_status == ComputeTask.Status.STATUS_DONE:
            factory.create_performance(
                test_task,
                self.metric_algo,
                identifier="performance",
            )

        return cp

    def create_aggregate_cp(self):
        logger.debug("  Create aggregate CP")
        # (train, train) -> aggregate
        cp = factory.create_computeplan(
            name="aggregate",
            status=ComputePlan.Status.PLAN_STATUS_TODO,
        )
        train_task_1 = factory.create_computetask(
            cp,
            self.simple_algo,
            inputs=factory.build_computetask_inputs(
                self.simple_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.train_data_sample_keys,
                },
            ),
            outputs=factory.build_computetask_outputs(self.simple_algo),
            data_manager=self.data_manager,
            data_samples=self.train_data_sample_keys,
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_TODO,
        )
        train_task_2 = factory.create_computetask(
            cp,
            self.simple_algo,
            inputs=factory.build_computetask_inputs(
                self.simple_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.train_data_sample_keys,
                },
            ),
            outputs=factory.build_computetask_outputs(self.simple_algo),
            data_manager=self.data_manager,
            data_samples=self.train_data_sample_keys,
            category=ComputeTask.Category.TASK_TRAIN,
            status=ComputeTask.Status.STATUS_TODO,
        )
        factory.create_computetask(
            cp,
            self.aggregate_algo,
            inputs=factory.build_computetask_inputs(
                self.aggregate_algo,
                {
                    "model": [train_task_1.key, train_task_2.key],
                },
            ),
            outputs=factory.build_computetask_outputs(self.aggregate_algo),
            category=ComputeTask.Category.TASK_AGGREGATE,
            status=ComputeTask.Status.STATUS_TODO,
        )
        return cp

    def create_composite_cp(self):
        logger.debug("  Create composite CP")
        cp = factory.create_computeplan(
            name="composite",
            status=ComputePlan.Status.PLAN_STATUS_DONE,
        )
        composite_task = factory.create_computetask(
            cp,
            self.composite_algo,
            inputs=factory.build_computetask_inputs(
                self.composite_algo,
                {
                    "opener": [self.data_manager.key],
                    "datasamples": self.train_data_sample_keys,
                },
            ),
            outputs=factory.build_computetask_outputs(self.composite_algo),
            data_manager=self.data_manager,
            data_samples=self.train_data_sample_keys,
            category=ComputeTask.Category.TASK_COMPOSITE,
            status=ComputeTask.Status.STATUS_DONE,
        )
        local_model = factory.create_model(
            composite_task,
            identifier="local",
        )
        factory.create_model_files(key=local_model.key)
        shared_model = factory.create_model(
            composite_task,
            identifier="shared",
        )
        factory.create_model_files(key=shared_model.key)
        return cp
