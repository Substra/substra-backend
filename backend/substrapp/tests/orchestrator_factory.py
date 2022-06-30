import factory
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.datamanager_pb2 as datamanager_pb2
import orchestrator.model_pb2 as model_pb2
from orchestrator.client import CONVERT_SETTINGS
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from substrapp.tests.factory import DEFAULT_OWNER
from substrapp.tests.factory import DEFAULT_WORKER
from substrapp.tests.factory import get_storage_address

OPEN_PERMISSIONS = common_pb2.Permissions(
    download=common_pb2.Permission(public=True, authorized_ids=[]),
    process=common_pb2.Permission(public=True, authorized_ids=[]),
)


# TODO: refactor with factory.py
ALGO_INPUTS_PER_CATEGORY = {
    algo_pb2.ALGO_SIMPLE: {
        "datasamples": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_SAMPLE, multiple=True, optional=False),
        "model": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=True),
        "opener": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_MANAGER, multiple=False, optional=False),
    },
    algo_pb2.ALGO_AGGREGATE: {
        "model": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=True, optional=False),
    },
    algo_pb2.ALGO_COMPOSITE: {
        "datasamples": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_SAMPLE, multiple=True, optional=False),
        "local": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=True),
        "opener": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_MANAGER, multiple=False, optional=False),
        "shared": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=True),
    },
    algo_pb2.ALGO_METRIC: {
        "datasamples": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_SAMPLE, multiple=True, optional=False),
        "opener": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_MANAGER, multiple=False, optional=False),
        "predictions": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=False),
    },
    algo_pb2.ALGO_PREDICT: {
        "datasamples": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_SAMPLE, multiple=True, optional=False),
        "opener": algo_pb2.AlgoInput(kind=common_pb2.ASSET_DATA_MANAGER, multiple=False, optional=False),
        "model": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=False),
        "shared": algo_pb2.AlgoInput(kind=common_pb2.ASSET_MODEL, multiple=False, optional=True),
    },
}

# TODO: refactor with factory.py
ALGO_OUTPUTS_PER_CATEGORY = {
    algo_pb2.ALGO_SIMPLE: {
        "model": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_MODEL, multiple=False),
    },
    algo_pb2.ALGO_AGGREGATE: {
        "model": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_MODEL, multiple=False),
    },
    algo_pb2.ALGO_COMPOSITE: {
        "local": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_MODEL, multiple=False),
        "shared": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_MODEL, multiple=False),
    },
    algo_pb2.ALGO_METRIC: {
        "performance": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_PERFORMANCE, multiple=False),
    },
    algo_pb2.ALGO_PREDICT: {
        "predictions": algo_pb2.AlgoOutput(kind=common_pb2.ASSET_MODEL, multiple=False),
    },
}


class Orchestrator:
    def __init__(self) -> None:
        self.client = MockOrchestratorClient()

    def create_algo(self, **kwargs):
        algo = AlgoFactory(**kwargs)
        self.client.algos[algo.key] = algo
        return algo

    def create_data_manager(self, **kwargs):
        data_manager = DataManagerFactory(**kwargs)
        self.client.data_managers[data_manager.key] = data_manager
        return data_manager

    def create_compute_plan(self, **kwargs):
        compute_plan = ComputePlanFactory(**kwargs)
        self.client.compute_plans[compute_plan.key] = compute_plan
        return compute_plan

    def create_model(self, **kwargs):
        model = ModelFactory(**kwargs)

        self.client.query_task(model.compute_task_key)

        self.client.models[model.key] = model
        return model

    def _create_common_task_dependencies(self, task: computetask_pb2.ComputeTask):
        if task.algo.key not in self.client.algos.keys():
            self.client.algos[task.algo.key] = task.algo

        if task.compute_plan_key not in self.client.compute_plans.keys():
            self.create_compute_plan(key=task.compute_plan_key)

    def create_train_task(self, **kwargs):
        compute_task = TrainTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        if compute_task.train.data_manager_key not in self.client.data_managers.keys():
            self.create_data_manager(key=compute_task.train.data_manager_key)

        if len(compute_task.parent_task_keys) > 1:
            raise OrcError()

        compute_task.inputs.append(
            computetask_pb2.ComputeTaskInput(identifier="data_manager", asset_key=compute_task.train.data_manager_key)
        )

        compute_task.inputs.extend(
            [
                computetask_pb2.ComputeTaskInput(identifier="datasamples", asset_key=key)
                for key in compute_task.train.data_sample_keys
            ]
        )

        for parent_task_key in compute_task.parent_task_keys:
            parent_task = self.client.tasks.get(parent_task_key)
            if not parent_task:
                raise OrcError()
            if parent_task.category == computetask_pb2.TASK_TRAIN:
                compute_task.inputs.append(
                    computetask_pb2.ComputeTaskInput(
                        identifier="model",
                        parent_task_output=computetask_pb2.ParentTaskOutputRef(
                            output_identifier="model", parent_task_key=parent_task_key
                        ),
                    )
                )
            else:
                raise OrcError()

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_composite_train_task(self, **kwargs):
        compute_task = CompositeTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        if compute_task.composite.data_manager_key not in self.client.data_managers.keys():
            self.create_data_manager(key=compute_task.composite.data_manager_key)

        if len(compute_task.parent_task_keys) > 2:
            raise OrcError()

        if len(compute_task.parent_task_keys) != 0 and len(compute_task.inputs) != 2:
            raise OrcError()

        if len(compute_task.parent_task_keys) == 0 and len(compute_task.inputs) != 0:
            raise OrcError()

        compute_task.inputs.append(
            computetask_pb2.ComputeTaskInput(
                identifier="data_manager", asset_key=compute_task.composite.data_manager_key
            )
        )

        compute_task.inputs.extend(
            [
                computetask_pb2.ComputeTaskInput(identifier="datasamples", asset_key=key)
                for key in compute_task.composite.data_sample_keys
            ]
        )

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_predict_task(self, **kwargs):
        compute_task = PredictTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        if compute_task.predict.data_manager_key not in self.client.data_managers.keys():
            self.create_data_manager(key=compute_task.predict.data_manager_key)

        compute_task.inputs.append(
            computetask_pb2.ComputeTaskInput(identifier="data_manager", asset_key=compute_task.predict.data_manager_key)
        )

        compute_task.inputs.extend(
            [
                computetask_pb2.ComputeTaskInput(identifier="datasamples", asset_key=key)
                for key in compute_task.predict.data_sample_keys
            ]
        )

        if len(compute_task.parent_task_keys) != 1:
            raise OrcError()

        parent_task = self.client.tasks.get(compute_task.parent_task_keys[0])
        if not parent_task:
            raise OrcError()

        if parent_task.category == computetask_pb2.TASK_TRAIN:
            compute_task.inputs.append(
                computetask_pb2.ComputeTaskInput(
                    identifier="model",
                    parent_task_output=computetask_pb2.ParentTaskOutputRef(
                        output_identifier="model", parent_task_key=parent_task.key
                    ),
                )
            )
        elif parent_task.category == computetask_pb2.TASK_COMPOSITE:
            compute_task.inputs.append(
                computetask_pb2.ComputeTaskInput(
                    identifier="shared",
                    parent_task_output=computetask_pb2.ParentTaskOutputRef(
                        output_identifier="shared", parent_task_key=parent_task.key
                    ),
                )
            )
            compute_task.inputs.append(
                computetask_pb2.ComputeTaskInput(
                    identifier="local",
                    parent_task_output=computetask_pb2.ParentTaskOutputRef(
                        output_identifier="local", parent_task_key=parent_task.key
                    ),
                )
            )
        else:
            raise OrcError()

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_test_task(self, **kwargs):
        if "parent_task_keys" not in kwargs:
            raise OrcError()

        parent_task = self.client.tasks.get(kwargs["parent_task_keys"][0])
        if not parent_task:
            raise OrcError()

        # TODO: remove this when splitting predict & test
        if parent_task.category in [computetask_pb2.TASK_TRAIN, computetask_pb2.TASK_COMPOSITE]:
            metric = self.create_algo(category=algo_pb2.ALGO_METRIC)
            kwargs["test"] = TestTaskDataFactory(metric_keys=[metric.key])
            kwargs["algo"] = parent_task.algo

        compute_task = TestTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        if compute_task.test.data_manager_key not in self.client.data_managers.keys():
            self.create_data_manager(key=compute_task.test.data_manager_key)

        compute_task.inputs.append(
            computetask_pb2.ComputeTaskInput(identifier="data_manager", asset_key=compute_task.test.data_manager_key)
        )

        compute_task.inputs.extend(
            [
                computetask_pb2.ComputeTaskInput(identifier="datasamples", asset_key=key)
                for key in compute_task.test.data_sample_keys
            ]
        )

        if len(compute_task.parent_task_keys) != 1:
            raise OrcError()

        if parent_task.category == computetask_pb2.TASK_PREDICT:
            compute_task.inputs.append(
                computetask_pb2.ComputeTaskInput(
                    identifier="predictions",
                    parent_task_output=computetask_pb2.ParentTaskOutputRef(
                        output_identifier="predictions", parent_task_key=parent_task.key
                    ),
                )
            )

        self.client.tasks[compute_task.key] = compute_task
        return compute_task


class MockOrchestratorClient(OrchestratorClient):
    def __init__(self, *args, **kwargs):
        del args, kwargs
        self.tasks: dict[str, computetask_pb2.ComputeTask] = {}
        self.compute_plans: dict[str, computeplan_pb2.ComputePlan] = {}
        self.models: dict[str, model_pb2.Model] = {}
        self.algos: dict[str, algo_pb2.Algo] = {}
        self.data_managers: dict[str, datamanager_pb2.DataManager] = {}

    def __exit__(self, *args):
        del args

    def query_task(self, key):
        task = self.tasks.get(key)
        if not task:
            raise OrcError()
        return MessageToDict(task, **CONVERT_SETTINGS)

    def query_compute_plan(self, key):  # noqa: C901
        cp = self.compute_plans.get(key)

        if not cp:
            raise OrcError()

        for task in self.tasks.values():
            if task.compute_plan_key == cp.key:
                if task.status == computetask_pb2.STATUS_WAITING:
                    cp.waiting_count = cp.waiting_count + 1
                elif task.status == computetask_pb2.STATUS_TODO:
                    cp.todo_count = cp.todo_count + 1
                elif task.status == computetask_pb2.STATUS_DOING:
                    cp.doing_count = cp.doing_count + 1
                elif task.status == computetask_pb2.STATUS_CANCELED:
                    cp.canceled_count = cp.canceled_count + 1
                elif task.status == computetask_pb2.STATUS_FAILED:
                    cp.failed_count = cp.failed_count + 1
                elif task.status == computetask_pb2.STATUS_DONE:
                    cp.done_count = cp.done_count + 1

                cp.task_count = cp.task_count + 1

        if cp.task_count == 0:
            cp.status = computeplan_pb2.PLAN_STATUS_EMPTY
        elif cp.failed_count > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_FAILED
        elif cp.canceled_count > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_CANCELED
        elif cp.doing_count > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_DOING
        elif cp.todo_count > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_TODO
        elif cp.waiting_count > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_WAITING
        else:
            cp.status = computeplan_pb2.PLAN_STATUS_DONE

        return MessageToDict(cp, **CONVERT_SETTINGS)

    def get_computetask_input_models(self, compute_task_key):
        task = self.tasks.get(compute_task_key)
        if not task:
            raise OrcError()

        models = [model for model in self.models.values() if model.compute_task_key in task.parent_task_keys]
        res = model_pb2.GetComputeTaskModelsResponse(models=models)
        return MessageToDict(res, **CONVERT_SETTINGS).get("models", [])

    def query_algo(self, key):
        algo = self.algos.get(key)
        if not algo:
            raise OrcError()

        return MessageToDict(algo, **CONVERT_SETTINGS)

    def query_datamanager(self, key):
        dm = self.data_managers.get(key)
        if not dm:
            raise OrcError()

        return MessageToDict(dm, **CONVERT_SETTINGS)

    def update_task_status(self, compute_task_key, action, log=""):
        del log
        task = self.tasks.get(compute_task_key)
        if not task:
            raise OrcError()
        action_to_status = {computetask_pb2.TASK_ACTION_DONE: computetask_pb2.STATUS_DONE}
        task.status = action_to_status[action]


class AddressableFactory(factory.Factory):
    class Meta:
        model = common_pb2.Addressable

    checksum = factory.Faker("sha256")
    storage_address = factory.Faker("url")


class DataManagerFactory(factory.Factory):
    class Meta:
        model = datamanager_pb2.DataManager

    key = factory.Faker("uuid4")
    name = factory.Faker("user_name")
    owner = DEFAULT_WORKER
    permissions = OPEN_PERMISSIONS
    description = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("data_manager", obj.key, "description"))
    )
    opener = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("data_manager", obj.key, "opener"))
    )
    type = "test"
    creation_date = Timestamp()
    logs_permission = common_pb2.Permission(public=True, authorized_ids=[])
    metadata = {}


class ModelFactory(factory.Factory):
    class Meta:
        model = model_pb2.Model

    key = factory.Faker("uuid4")
    category = model_pb2.MODEL_SIMPLE
    compute_task_key = factory.Faker("uuid4")
    address = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("model", obj.key, "model"))
    )
    permissions = OPEN_PERMISSIONS
    owner = DEFAULT_WORKER
    creation_date = Timestamp()


class ComputePlanFactory(factory.Factory):
    class Meta:
        model = computeplan_pb2.ComputePlan

    key = factory.Faker("uuid4")
    owner = DEFAULT_OWNER
    waiting_count = 0
    todo_count = 0
    doing_count = 0
    canceled_count = 0
    failed_count = 0
    done_count = 0
    task_count = 0
    status = computeplan_pb2.PLAN_STATUS_EMPTY
    delete_intermediary_models = False
    creation_date = Timestamp()
    tag = ""
    name = factory.Faker("user_name")
    metadata = {}


class AlgoFactory(factory.Factory):
    class Meta:
        model = algo_pb2.Algo

    key = factory.Faker("uuid4")
    name = factory.Faker("user_name")
    category = algo_pb2.ALGO_UNKNOWN
    description = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("algo", obj.key, "description"))
    )
    algorithm = factory.LazyAttribute(
        lambda obj: AddressableFactory(storage_address=get_storage_address("algo", obj.key, "algorithm"))
    )
    permissions = OPEN_PERMISSIONS
    owner = DEFAULT_OWNER
    creation_date = Timestamp()
    metadata = {}
    inputs = factory.LazyAttribute(lambda obj: ALGO_INPUTS_PER_CATEGORY[obj.category])
    outputs = factory.LazyAttribute(lambda obj: ALGO_OUTPUTS_PER_CATEGORY[obj.category])


class ComputeTaskOutputFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.ComputeTaskOutput

    permissions = OPEN_PERMISSIONS


class TaskFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.ComputeTask

    key = factory.Faker("uuid4")
    owner = DEFAULT_OWNER
    compute_plan_key = factory.Faker("uuid4")
    parent_task_keys = []
    rank = 0
    status = computetask_pb2.STATUS_WAITING
    worker = DEFAULT_WORKER
    creation_date = Timestamp()
    logs_permission = common_pb2.Permission(public=True, authorized_ids=[])
    metadata = {}


class TrainTaskDataFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.TrainTaskData

    data_manager_key = factory.Faker("uuid4")
    data_sample_keys = factory.List([factory.Faker("uuid4"), factory.Faker("uuid4")])


class TrainTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_TRAIN
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_SIMPLE)
    train = factory.SubFactory(TrainTaskDataFactory)
    inputs = []
    outputs = {"model": ComputeTaskOutputFactory()}


class CompositeTaskDataFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.CompositeTrainTaskData

    data_manager_key = factory.Faker("uuid4")
    data_sample_keys = factory.List([factory.Faker("uuid4"), factory.Faker("uuid4")])


class CompositeTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_COMPOSITE
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_COMPOSITE)
    composite = factory.SubFactory(CompositeTaskDataFactory)
    inputs = []
    outputs = {"head": ComputeTaskOutputFactory(), "trunk": ComputeTaskOutputFactory()}


class PredictTaskDataFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.PredictTaskData

    data_manager_key = factory.Faker("uuid4")
    data_sample_keys = factory.List([factory.Faker("uuid4"), factory.Faker("uuid4")])


class PredictTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_PREDICT
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_PREDICT)
    predict = factory.SubFactory(PredictTaskDataFactory)
    inputs = []
    outputs = {"predictions": ComputeTaskOutputFactory()}


class TestTaskDataFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.TestTaskData

    data_manager_key = factory.Faker("uuid4")
    data_sample_keys = factory.List([factory.Faker("uuid4"), factory.Faker("uuid4")])
    metric_keys = []


class TestTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_TEST
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_METRIC)
    test = factory.SubFactory(TestTaskDataFactory)
    inputs = []
    outputs = {"performance": ComputeTaskOutputFactory()}
