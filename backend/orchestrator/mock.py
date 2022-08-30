import factory

from .resources import Address
from .resources import Algo
from .resources import ComputePlan
from .resources import ComputePlanStatus
from .resources import ComputeTask
from .resources import ComputeTaskCategory
from .resources import ComputeTaskStatus
from .resources import DataManager
from .resources import DataSample
from .resources import Model


class ComputeTaskFactory(factory.Factory):
    class Meta:
        model = ComputeTask

    key = factory.Faker("uuid4")
    category = ComputeTaskCategory.TASK_TRAIN
    owner = "OrgA"
    compute_plan_key = factory.Faker("uuid4")
    algo_key = factory.Faker("uuid4")
    rank = 0
    status = ComputeTaskStatus.STATUS_TODO
    worker = "OrgA"
    metadata = {}
    inputs = []
    outputs = {}
    tag = ""


class AddressFactory(factory.Factory):
    class Meta:
        model = Address

    checksum = factory.Faker("sha256")
    uri = factory.Faker("url")


class ModelFactory(factory.Factory):
    class Meta:
        model = Model

    key = factory.Faker("uuid4")
    compute_task_key = factory.Faker("uuid4")
    address = factory.SubFactory(AddressFactory)


class DataSampleFactory(factory.Factory):
    class Meta:
        model = DataSample

    key = factory.Faker("uuid4")


class DataManagerFactory(factory.Factory):
    class Meta:
        model = DataManager

    key = factory.Faker("uuid4")
    opener = factory.SubFactory(AddressFactory)


class AlgoFactory(factory.Factory):
    class Meta:
        model = Algo

    key = factory.Faker("uuid4")
    owner = "OrgA"
    algorithm = factory.SubFactory(AddressFactory)


class ComputePlanFactory(factory.Factory):
    class Meta:
        model = ComputePlan

    key = factory.Faker("uuid4")
    tag = ""
    status = ComputePlanStatus.PLAN_STATUS_DOING
