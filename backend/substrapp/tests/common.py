import base64
import os
import urllib
from dataclasses import dataclass
from http.cookies import SimpleCookie
from io import BytesIO
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from google.protobuf.json_format import MessageToDict
from requests import auth
from rest_framework.test import APIClient

import orchestrator.algo_pb2 as algo_pb2
from orchestrator import computetask_pb2 as computetask_pb2
from orchestrator import model_pb2 as model_pb2
from orchestrator.algo_pb2 import ALGO_AGGREGATE
from orchestrator.algo_pb2 import ALGO_COMPOSITE
from orchestrator.algo_pb2 import ALGO_METRIC
from orchestrator.algo_pb2 import ALGO_PREDICT
from orchestrator.algo_pb2 import ALGO_SIMPLE
from orchestrator.algo_pb2 import AlgoInput
from orchestrator.algo_pb2 import AlgoOutput
from orchestrator.client import CONVERT_SETTINGS
from orchestrator.common_pb2 import ASSET_DATA_MANAGER
from orchestrator.common_pb2 import ASSET_DATA_SAMPLE
from orchestrator.common_pb2 import ASSET_MODEL
from orchestrator.common_pb2 import ASSET_PERFORMANCE
from organization.models import IncomingOrganization
from users.models.user_channel import UserChannel

# This function helper generate a basic authentication header with given credentials
# Given username and password it returns "Basic GENERATED_TOKEN"
from users.serializers import CustomTokenObtainPairSerializer

_TASK_CATEGORY_NAME_TRAIN = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN)
_TASK_CATETGORY_NAME_COMPOSITE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_COMPOSITE)
_TASK_CATEGORY_NAME_AGGREGATE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_AGGREGATE)

_MODEL_CATEGORY_NAME_SIMPLE = model_pb2.ModelCategory.Name(model_pb2.MODEL_SIMPLE)
_MODEL_CATEGORY_NAME_HEAD = model_pb2.ModelCategory.Name(model_pb2.MODEL_HEAD)


@dataclass
class InputIdentifiers:
    DATASAMPLES = "datasamples"
    LOCAL = "local"
    MODEL = "model"
    OPENER = "opener"
    PERFORMANCE = "performance"
    PREDICTIONS = "predictions"
    SHARED = "shared"


# Algo inputs, protobuf format
ALGO_INPUTS_PER_CATEGORY = {
    ALGO_SIMPLE: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
    },
    ALGO_AGGREGATE: {
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=True, optional=False),
    },
    ALGO_COMPOSITE: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.LOCAL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.SHARED: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
    },
    ALGO_METRIC: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.PREDICTIONS: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=False),
    },
    ALGO_PREDICT: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=False),
        InputIdentifiers.SHARED: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
    },
}


# Algo outputs, protobuf format
ALGO_OUTPUTS_PER_CATEGORY = {
    ALGO_SIMPLE: {
        InputIdentifiers.MODEL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    ALGO_AGGREGATE: {
        InputIdentifiers.MODEL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    ALGO_COMPOSITE: {
        InputIdentifiers.LOCAL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
        InputIdentifiers.SHARED: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    ALGO_METRIC: {
        InputIdentifiers.PERFORMANCE: AlgoOutput(kind=ASSET_PERFORMANCE, multiple=False),
    },
    ALGO_PREDICT: {
        InputIdentifiers.PREDICTIONS: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
}

# Algo inputs, dictionary format
ALGO_INPUTS_PER_CATEGORY_DICT: dict[str, dict] = {
    algo_pb2.AlgoCategory.Name(category): {
        identifier: MessageToDict(input_proto, **CONVERT_SETTINGS)
        for identifier, input_proto in inputs_by_identifier.items()
    }
    for category, inputs_by_identifier in ALGO_INPUTS_PER_CATEGORY.items()
}

# Algo outputs, dictionary format
ALGO_OUTPUTS_PER_CATEGORY_DICT: dict[str, dict] = {
    algo_pb2.AlgoCategory.Name(category): {
        identifier: MessageToDict(output_proto, **CONVERT_SETTINGS)
        for identifier, output_proto in outputs_by_identifier.items()
    }
    for category, outputs_by_identifier in ALGO_OUTPUTS_PER_CATEGORY.items()
}


def generate_basic_auth_header(username, password):
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def generate_jwt_auth_header(jwt):
    return "JWT " + jwt


class AuthenticatedClient(APIClient):
    def __init__(self, enforce_csrf_checks=False, role=UserChannel.Role.USER, channel=None, **defaults):
        super().__init__(enforce_csrf_checks, **defaults)
        self.role = role
        self.channel = channel

    def request(self, **kwargs):
        # create user
        username = "substra"
        password = "p@sswr0d44"
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            # for testing purpose most authentication are done without channel allowing to mock passing channel in
            # header, this check is necessary to not break previous tests but irl a user cannot be created
            # without a channel
            if self.channel:
                UserChannel.objects.create(user=user, channel_name=self.channel, role=self.role)

        # simulate login
        serializer = CustomTokenObtainPairSerializer(data={"username": username, "password": password})

        serializer.is_valid()
        data = serializer.validated_data
        access_token = str(data.access_token)

        # simulate right httpOnly cookie and Authorization jwt
        jwt_auth_header = generate_jwt_auth_header(".".join(access_token.split(".")[0:2]))
        self.credentials(HTTP_AUTHORIZATION=jwt_auth_header)
        self.cookies = SimpleCookie({"signature": access_token.split(".")[2]})

        return super().request(**kwargs)


class AuthenticatedBackendClient(APIClient):
    def request(self, **kwargs):

        username = "MyTestOrg"
        password = "p@sswr0d44"
        try:
            IncomingOrganization.objects.get(organization_id=username)
        except IncomingOrganization.DoesNotExist:
            IncomingOrganization.objects.create(organization_id=username, secret=password)

        self.credentials(HTTP_AUTHORIZATION=auth._basic_auth_str(username, password))

        return super().request(**kwargs)


def get_temporary_text_file(contents, filename):
    """
    Creates a temporary text file

    :param contents: contents of the file
    :param filename: name of the file
    :type contents: str
    :type filename: str
    """
    f = StringIO()
    flength = f.write(contents)
    text_file = InMemoryUploadedFile(f, None, filename, "text", flength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


def get_sample_metric():

    dir_path = os.path.dirname(os.path.realpath(__file__))

    description_content = "Super metric"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)

    metrics_filename = "metrics.zip"
    f = BytesIO(b"")
    with open(os.path.join(dir_path, "../../../fixtures/chunantes/metrics/metric0/metrics.zip"), "rb") as zip_file:
        flength = f.write(zip_file.read())
    metrics = InMemoryUploadedFile(f, None, metrics_filename, "application/zip", flength, None)
    metrics.seek(0)

    return description, description_filename, metrics, metrics_filename


def get_sample_script():
    script_content = "import slidelib\n\ndef read():\n\tpass"
    script_filename = "script.py"
    script = get_temporary_text_file(script_content, script_filename)

    return script, script_filename


def get_sample_datamanager():
    description_content = "description"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_datamanager2():
    description_content = "description 2"
    description_filename = "description2.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import os\nimport slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener2.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_zip_data_sample():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO(b"foo")
    with open(os.path.join(dir_path, "../../../fixtures/owkin/datasamples/datasample4/0024900.zip"), "rb") as zip_file:
        flength = f.write(zip_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/zip", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_zip_data_sample_2():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO(b"foo")
    with open(os.path.join(dir_path, "../../../fixtures/owkin/datasamples/test/0024901.zip"), "rb") as zip_file:
        flength = f.write(zip_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/zip", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_tar_data_sample():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(
        os.path.join(dir_path, "../../../fixtures/owkin/datasamples/datasample4/0024900.tar.gz"), "rb"
    ) as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/zip", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_algo():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(os.path.join(dir_path, "../../../fixtures/chunantes/algos/algo3/algo.tar.gz"), "rb") as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/tar+gzip", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_algo_zip():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO()
    with open(os.path.join(dir_path, "../../../fixtures/chunantes/algos/algo0/algo.zip"), "rb") as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/zip", flength, None)
    file.seek(0)

    return file, file_filename


def get_description_algo():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.md"
    f = BytesIO()
    with open(os.path.join(dir_path, "../../../fixtures/chunantes/algos/algo3/description.md"), "rb") as desc_file:
        flength = f.write(desc_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/text", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_model():
    model_content = "0.1, 0.2, -1.0"
    model_filename = "model.bin"
    model = get_temporary_text_file(model_content, model_filename)

    return model, model_filename


DEFAULT_PERMISSIONS = {
    "process": {
        "public": True,
        "authorized_ids": [],
    }
}

DEFAULT_STORAGE_ADDRESS = {
    "checksum": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
    "storage_address": "http://fake_address.com",
}


def get_sample_algo_metadata():
    return {
        "owner": "foo",
        "permissions": DEFAULT_PERMISSIONS,
        "description": DEFAULT_STORAGE_ADDRESS,
        "algorithm": DEFAULT_STORAGE_ADDRESS,
    }


def get_sample_metric_metadata():
    return {
        "owner": "foo",
        "permissions": DEFAULT_PERMISSIONS,
        "description": DEFAULT_STORAGE_ADDRESS,
        "address": DEFAULT_STORAGE_ADDRESS,
    }


def get_sample_datamanager_metadata():
    return {
        "owner": "foo",
        "permissions": DEFAULT_PERMISSIONS,
        "description": DEFAULT_STORAGE_ADDRESS,
        "opener": DEFAULT_STORAGE_ADDRESS,
    }


class FakeMetrics(object):
    def __init__(self, filepath="path"):
        self.path = filepath

    def save(self, p, f):
        return

    def read(self, *args, **kwargs):
        return b"foo"


class FakeMetric(object):
    def __init__(self, filepath="path"):
        self.file = FakeMetrics(filepath)


class FakeDataManager(object):
    def __init__(self, file, checksum):
        self.data_opener = file
        self.checksum = checksum


class FakeDataSample(object):
    def __init__(self, file=None, path=None, checksum=None):
        self.file = file
        self.path = path
        self.checksum = checksum


class FakeFilterDataManager(object):
    def __init__(self, count):
        self.count_value = count

    def count(self):
        return self.count_value


class FakeModel(object):
    def __init__(self, file, checksum):
        self.file = file
        self.checksum = checksum


class FakeRequest(object):
    def __init__(self, status, content):
        self.status_code = status
        self.content = content


def encode_filter(params):
    # We need to quote the params string because the filter function
    # in the backend use the same  ':' url separator for key:value filtering object
    return urllib.parse.quote(params)


def internal_server_error_on_exception():
    """Decorator factory to make the Django test client respond with '500 Internal Server Error'
    when an unhandled exception occurs.

    Once we update to Django 3, we can use the `raise_request_exception` parameter
    of the test client: https://docs.djangoproject.com/en/3.2/topics/testing/tools/#making-requests.

    Adapted from https://stackoverflow.com/a/62720158.
    """
    return mock.patch("django.test.client.Client.store_exc_info", mock.Mock())
