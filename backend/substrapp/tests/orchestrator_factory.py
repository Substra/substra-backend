import factory
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp

import orchestrator
import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.datamanager_pb2 as datamanager_pb2
import orchestrator.datasample_pb2 as datasample_pb2
import orchestrator.model_pb2 as model_pb2
from orchestrator.client import CONVERT_SETTINGS
from orchestrator.client import OrchestratorClient
from orchestrator.error import OrcError
from orchestrator.resources import ComputeTaskInputAsset
from substrapp.tests import common
from substrapp.tests.common import InputIdentifiers

OPEN_PERMISSIONS = common_pb2.Permissions(
    download=common_pb2.Permission(public=True, authorized_ids=[]),
    process=common_pb2.Permission(public=True, authorized_ids=[]),
)

ALGO_INPUTS_PER_CATEGORY = common.ALGO_INPUTS_PER_CATEGORY
ALGO_OUTPUTS_PER_CATEGORY = common.ALGO_OUTPUTS_PER_CATEGORY

DEFAULT_OWNER = "MyOrg1MSP"
DEFAULT_WORKER = "MyOrg1MSP"


def get_storage_address(asset_kind: str, key: str, field: str) -> str:
    return f"http://testserver/{asset_kind}/{key}/{field}/"


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

    def set_input_assets(self, task_key: str, inputs: list[ComputeTaskInputAsset]):
        self.client.input_assets[task_key] = inputs

    def build_task_inputs(
        self, input_models: list[computetask_pb2.ComputeTaskInput] = None, with_data=True
    ) -> list[computetask_pb2.ComputeTaskInput]:
        inputs = input_models or []
        if with_data:
            inputs += [
                self.create_task_input(identifier=InputIdentifiers.OPENER, asset_key=self.create_data_manager().key)
            ]
            inputs += [self.create_task_input(identifier=InputIdentifiers.DATASAMPLES) for _ in range(3)]
        return inputs

    def create_task_input(self, parent_task_key: str = None, parent_task_output_identifier: str = None, **kwargs):
        if parent_task_key:
            kwargs["parent_task_output"] = computetask_pb2.ParentTaskOutputRef(
                parent_task_key=parent_task_key, output_identifier=parent_task_output_identifier
            )
        return ComputeTaskInputFactory(**kwargs)

    def _create_common_task_dependencies(self, task: computetask_pb2.ComputeTask):
        if task.algo.key not in self.client.algos.keys():
            self.client.algos[task.algo.key] = task.algo

        if task.compute_plan_key not in self.client.compute_plans.keys():
            self.create_compute_plan(key=task.compute_plan_key)

    def create_train_task(self, **kwargs):
        compute_task = TrainTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_composite_train_task(self, **kwargs):
        compute_task = CompositeTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_predict_task(self, **kwargs):
        compute_task = PredictTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

        self.client.tasks[compute_task.key] = compute_task
        return compute_task

    def create_test_task(self, **kwargs):
        kwargs["algo"] = self.create_algo(category=algo_pb2.ALGO_METRIC)

        compute_task = TestTaskFactory(**kwargs)

        self._create_common_task_dependencies(compute_task)

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
        self.input_assets: dict[str, list[computetask_pb2.ComputeTaskInputAsset]] = {}

    def __exit__(self, *args):
        del args

    def query_task(self, key):
        task = self.tasks.get(key)
        if not task:
            raise OrcError()
        return orchestrator.ComputeTask.from_grpc(task)

    def query_compute_plan(self, key):  # noqa: C901
        cp = self.compute_plans.get(key)

        status_counts = {
            computetask_pb2.STATUS_WAITING: 0,
            computetask_pb2.STATUS_TODO: 0,
            computetask_pb2.STATUS_DOING: 0,
            computetask_pb2.STATUS_CANCELED: 0,
            computetask_pb2.STATUS_FAILED: 0,
            computetask_pb2.STATUS_DONE: 0,
        }
        total_count = 0

        if not cp:
            raise OrcError()

        for task in self.tasks.values():
            if task.compute_plan_key == cp.key:
                status_counts[task.status] += 1
                total_count += 1

        if total_count == 0:
            cp.status = computeplan_pb2.PLAN_STATUS_EMPTY
        elif status_counts[computetask_pb2.STATUS_FAILED] > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_FAILED
        elif status_counts[computetask_pb2.STATUS_FAILED] > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_CANCELED
        elif status_counts[computetask_pb2.STATUS_DOING] > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_DOING
        elif status_counts[computetask_pb2.STATUS_TODO] > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_TODO
        elif status_counts[computetask_pb2.STATUS_WAITING] > 0:
            cp.status = computeplan_pb2.PLAN_STATUS_WAITING
        else:
            cp.status = computeplan_pb2.PLAN_STATUS_DONE

        return orchestrator.ComputePlan.from_grpc(cp)

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

    def get_task_input_assets(self, task_key: str) -> list[ComputeTaskInputAsset]:
        return self.input_assets.get(task_key, [])


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
        lambda obj: AddressableFactory(
            storage_address=get_storage_address("data_manager", obj.key, InputIdentifiers.OPENER)
        )
    )
    type = "test"
    creation_date = Timestamp()
    logs_permission = common_pb2.Permission(public=True, authorized_ids=[])
    metadata = {}


class DataSampleFactory(factory.Factory):
    class Meta:
        model = datasample_pb2.DataSample

    key = factory.Faker("uuid4")
    owner = DEFAULT_OWNER
    checksum = factory.Faker("sha256")
    creation_date = Timestamp()
    test_only = False
    data_manager_keys = []


class ModelFactory(factory.Factory):
    class Meta:
        model = model_pb2.Model

    key = factory.Faker("uuid4")
    category = model_pb2.MODEL_SIMPLE
    compute_task_key = factory.Faker("uuid4")
    address = factory.LazyAttribute(
        lambda obj: AddressableFactory(
            storage_address=get_storage_address(InputIdentifiers.MODEL, obj.key, InputIdentifiers.MODEL)
        )
    )
    permissions = OPEN_PERMISSIONS
    owner = DEFAULT_WORKER
    creation_date = Timestamp()


class ComputePlanFactory(factory.Factory):
    class Meta:
        model = computeplan_pb2.ComputePlan

    key = factory.Faker("uuid4")
    owner = DEFAULT_OWNER
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


class ComputeTaskInputFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.ComputeTaskInput

    asset_key = factory.Faker("uuid4")


class TaskFactory(factory.Factory):
    class Meta:
        model = computetask_pb2.ComputeTask

    key = factory.Faker("uuid4")
    owner = DEFAULT_OWNER
    compute_plan_key = factory.Faker("uuid4")
    rank = 0
    status = computetask_pb2.STATUS_WAITING
    worker = DEFAULT_WORKER
    creation_date = Timestamp()
    logs_permission = common_pb2.Permission(public=True, authorized_ids=[])
    metadata = {}


class TrainTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_TRAIN
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_SIMPLE)
    inputs = []
    outputs = {InputIdentifiers.MODEL: ComputeTaskOutputFactory()}


class CompositeTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_COMPOSITE
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_COMPOSITE)
    inputs = []
    outputs = {InputIdentifiers.LOCAL: ComputeTaskOutputFactory(), InputIdentifiers.SHARED: ComputeTaskOutputFactory()}


class PredictTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_PREDICT
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_PREDICT)
    inputs = []
    outputs = {InputIdentifiers.PREDICTIONS: ComputeTaskOutputFactory()}


class TestTaskFactory(TaskFactory):
    category = computetask_pb2.TASK_TEST
    algo = factory.SubFactory(AlgoFactory, category=algo_pb2.ALGO_METRIC)
    inputs = []
    outputs = {InputIdentifiers.PERFORMANCE: ComputeTaskOutputFactory()}
