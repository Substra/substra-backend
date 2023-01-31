import factory

from .resources import Address
from .resources import AssetKind
from .resources import ComputePlan
from .resources import ComputeTask
from .resources import ComputeTaskInput
from .resources import ComputeTaskOutput
from .resources import ComputeTaskStatus
from .resources import DataManager
from .resources import DataSample
from .resources import Function
from .resources import FunctionInput
from .resources import Model
from .resources import Permission
from .resources import Permissions


class ComputeTaskInputFactory(factory.Factory):
    class Meta:
        model = ComputeTaskInput

    identifier = "model"
    asset_key = None
    parent_task_key = None
    parent_task_output_identifier = None


class ComputeTaskFactory(factory.Factory):
    class Meta:
        model = ComputeTask

    key = factory.Faker("uuid4")
    owner = "OrgA"
    compute_plan_key = factory.Faker("uuid4")
    function_key = factory.Faker("uuid4")
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
    owner = "OrgA"


class DataSampleFactory(factory.Factory):
    class Meta:
        model = DataSample

    key = factory.Faker("uuid4")


class DataManagerFactory(factory.Factory):
    class Meta:
        model = DataManager

    key = factory.Faker("uuid4")
    opener = factory.SubFactory(AddressFactory)


class FunctionInputFactory(factory.Factory):
    class Meta:
        model = FunctionInput

    kind = AssetKind.ASSET_MODEL
    multiple = False
    optional = True


class FunctionFactory(factory.Factory):
    class Meta:
        model = Function

    key = factory.Faker("uuid4")
    owner = "OrgA"
    functionrithm = factory.SubFactory(AddressFactory)
    inputs = {}
    outputs = {}


class ComputePlanFactory(factory.Factory):
    class Meta:
        model = ComputePlan

    key = factory.Faker("uuid4")
    tag = ""
    cancelation_date = None
    failure_date = None


class PermissionFactory(factory.Factory):
    class Meta:
        model = Permission

    public = True
    authorized_ids = []


class PermissionsFactory(factory.Factory):
    class Meta:
        model = Permissions

    process = factory.SubFactory(PermissionFactory)
    download = factory.SubFactory(PermissionFactory)


class ComputeTaskOutputFactory(factory.Factory):
    class Meta:
        model = ComputeTaskOutput

    transient = False
    permissions = factory.SubFactory(PermissionsFactory)
