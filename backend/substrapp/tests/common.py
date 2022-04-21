import base64
import os
import urllib
from http.cookies import SimpleCookie
from io import BytesIO
from io import StringIO
from typing import Dict
from typing import List
from typing import Optional
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.test import APIClient

from orchestrator import computetask_pb2 as computetask_pb2
from orchestrator import model_pb2 as model_pb2

# This function helper generate a basic authentication header with given credentials
# Given username and password it returns "Basic GENERATED_TOKEN"
from users.serializers import CustomTokenObtainPairSerializer

from . import assets

_TASK_CATEGORY_NAME_TRAIN = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_TRAIN)
_TASK_CATETGORY_NAME_COMPOSITE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_COMPOSITE)
_TASK_CATEGORY_NAME_AGGREGATE = computetask_pb2.ComputeTaskCategory.Name(computetask_pb2.TASK_AGGREGATE)

_MODEL_CATEGORY_NAME_SIMPLE = model_pb2.ModelCategory.Name(model_pb2.MODEL_SIMPLE)
_MODEL_CATEGORY_NAME_HEAD = model_pb2.ModelCategory.Name(model_pb2.MODEL_HEAD)


def generate_basic_auth_header(username, password):
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def generate_jwt_auth_header(jwt):
    return "JWT " + jwt


class AuthenticatedClient(APIClient):
    def request(self, **kwargs):

        # create user
        username = "substra"
        password = "p@sswr0d44"
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
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


def get_all_tasks() -> List:
    return assets.get_train_tasks() + assets.get_composite_tasks() + assets.get_test_tasks()


def get_algo(key: str) -> Optional[Dict]:
    for algo in assets.get_algos():
        if algo["key"] == key:
            return algo


def get_compute_plan(key: str) -> Optional[Dict]:
    for cp in assets.get_compute_plans():
        if cp["key"] == key:
            return cp


def get_task(key: str) -> Optional[Dict]:
    for task in get_all_tasks():
        if task["key"] == key:
            return task


def get_data_manager(key: str) -> Optional[Dict]:
    for dm in assets.get_data_managers():
        if dm["key"] == key:
            return dm


def get_metric(key: str) -> Optional[Dict]:
    for metric in assets.get_metrics():
        if metric["key"] == key:
            return metric


def get_model(key: str) -> Optional[Dict]:
    for model in assets.get_models():
        if model["key"] == key:
            return model


def get_task_events(task_key: str) -> Optional[List]:
    for task in get_all_tasks():
        if task["key"] == task_key:
            return [
                {
                    "metadata": {"status": "STATUS_DOING"},
                    "timestamp": task["start_date"],
                },
                {
                    "metadata": {"status": "STATUS_DONE"},
                    "timestamp": task["end_date"],
                },
            ]


def get_task_output_models(task_key: str) -> Optional[List]:
    for task in get_all_tasks():
        if task["key"] == task_key:
            return task.get("train", task.get("composite", {})).get("models")


def get_task_performances(task_key: str) -> Optional[List]:
    for task in get_all_tasks():
        if task["key"] == task_key and task["test"]["perfs"]:
            return [
                {"metric_key": perf_key, "performance_value": perf_value}
                for (perf_key, perf_value) in task["test"]["perfs"].items()
            ]


def get_test_task_input_models(task: Dict) -> List:
    # This logic is copied from the orchestrator

    res = []

    for parent_task_key in task["parent_task_keys"]:
        parent_task = get_task(parent_task_key)

        if parent_task["category"] == _TASK_CATEGORY_NAME_TRAIN:
            res += [m for m in parent_task["train"]["models"] if m["category"] == _MODEL_CATEGORY_NAME_SIMPLE]

        elif parent_task["category"] == _TASK_CATETGORY_NAME_COMPOSITE:

            models = parent_task["composite"]["models"]

            # For this function the order of assets is important we should always have the HEAD MODEL first in the list
            # Otherwise we end up feeding the head and trunk from the previous composite, ignoring the aggregate
            head_models = [m for m in models if m["category"] == _MODEL_CATEGORY_NAME_HEAD]
            if head_models:
                head_model = head_models[0]
                models.remove(head_model)
                models = [head_model] + models

            # True if the parent has contributed an input to the composite task
            parent_contributed = False

            for m in models:
                # Head model should always come from the first parent possible
                if m["category"] == _MODEL_CATEGORY_NAME_HEAD and not [
                    m2 for m2 in res if m2["category"] == _MODEL_CATEGORY_NAME_HEAD
                ]:
                    res.append(m)
                    parent_contributed = True

                single_parent = len(task["parent_task_keys"]) == 1
                complete_inputs = len(res) < 2

                # Add trunk from parent if it's a single parent or if we still miss an input and the parent has not
                # contributed a model yet.
                # Current parent should contribute the trunk model if:
                # - it's a single parent
                # - it has not contributed yet but not all inputs are set
                should_contribute_trunk = single_parent or (not parent_contributed and complete_inputs)

                if m["category"] == _MODEL_CATEGORY_NAME_SIMPLE and should_contribute_trunk:
                    res.append(m)
                    parent_contributed = True

        elif parent_task["category"] == _TASK_CATEGORY_NAME_AGGREGATE:
            res += parent_task["aggregate"]["models"]

    return res


def get_task_metrics(task: Dict) -> List:
    res = []
    for metric_key in task["test"]["metric_keys"]:
        res.append(get_metric(metric_key))
    return res


def internal_server_error_on_exception():
    """Decorator factory to make the Django test client respond with '500 Internal Server Error'
    when an unhandled exception occurs.

    Once we update to Django 3, we can use the `raise_request_exception` parameter
    of the test client: https://docs.djangoproject.com/en/3.2/topics/testing/tools/#making-requests.

    Adapted from https://stackoverflow.com/a/62720158.
    """
    return mock.patch("django.test.client.Client.store_exc_info", mock.Mock())
