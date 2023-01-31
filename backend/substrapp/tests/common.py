import os
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from io import StringIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from google.protobuf.json_format import MessageToDict

from orchestrator.client import CONVERT_SETTINGS
from orchestrator.common_pb2 import ASSET_DATA_MANAGER
from orchestrator.common_pb2 import ASSET_DATA_SAMPLE
from orchestrator.common_pb2 import ASSET_MODEL
from orchestrator.common_pb2 import ASSET_PERFORMANCE
from orchestrator.function_pb2 import AlgoInput
from orchestrator.function_pb2 import AlgoOutput


@dataclass
class InputIdentifiers:
    DATASAMPLES = "datasamples"
    LOCAL = "local"
    MODEL = "model"
    OPENER = "opener"
    PERFORMANCE = "performance"
    PREDICTIONS = "predictions"
    SHARED = "shared"


class AlgoCategory(str, Enum):
    simple = "ALGO_SIMPLE"
    composite = "ALGO_COMPOSITE"
    aggregate = "ALGO_AGGREGATE"
    metric = "ALGO_METRIC"
    predict = "ALGO_PREDICT"
    predict_composite = "ALGO_PREDICT_COMPOSITE"


# Function inputs, protobuf format
ALGO_INPUTS_PER_CATEGORY = {
    AlgoCategory.simple: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
    },
    AlgoCategory.aggregate: {
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=True, optional=False),
    },
    AlgoCategory.composite: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.LOCAL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.SHARED: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
    },
    AlgoCategory.metric: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.PREDICTIONS: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=False),
    },
    AlgoCategory.predict: {
        InputIdentifiers.DATASAMPLES: AlgoInput(kind=ASSET_DATA_SAMPLE, multiple=True, optional=False),
        InputIdentifiers.OPENER: AlgoInput(kind=ASSET_DATA_MANAGER, multiple=False, optional=False),
        InputIdentifiers.MODEL: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=False),
        InputIdentifiers.SHARED: AlgoInput(kind=ASSET_MODEL, multiple=False, optional=True),
    },
}


# Function outputs, protobuf format
ALGO_OUTPUTS_PER_CATEGORY = {
    AlgoCategory.simple: {
        InputIdentifiers.MODEL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    AlgoCategory.aggregate: {
        InputIdentifiers.MODEL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    AlgoCategory.composite: {
        InputIdentifiers.LOCAL: AlgoOutput(kind=ASSET_MODEL, multiple=False),
        InputIdentifiers.SHARED: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
    AlgoCategory.metric: {
        InputIdentifiers.PERFORMANCE: AlgoOutput(kind=ASSET_PERFORMANCE, multiple=False),
    },
    AlgoCategory.predict: {
        InputIdentifiers.PREDICTIONS: AlgoOutput(kind=ASSET_MODEL, multiple=False),
    },
}

# Function inputs, dictionary format
ALGO_INPUTS_PER_CATEGORY_DICT: dict[str, dict] = {
    category: {
        identifier: MessageToDict(input_proto, **CONVERT_SETTINGS)
        for identifier, input_proto in inputs_by_identifier.items()
    }
    for category, inputs_by_identifier in ALGO_INPUTS_PER_CATEGORY.items()
}

# Function outputs, dictionary format
ALGO_OUTPUTS_PER_CATEGORY_DICT: dict[str, dict] = {
    category: {
        identifier: MessageToDict(output_proto, **CONVERT_SETTINGS)
        for identifier, output_proto in outputs_by_identifier.items()
    }
    for category, outputs_by_identifier in ALGO_OUTPUTS_PER_CATEGORY.items()
}


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


def get_sample_function():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(
        os.path.join(dir_path, "../../../fixtures/chunantes/functions/function3/function.tar.gz"), "rb"
    ) as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/tar+gzip", flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_function_zip():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO()
    with open(os.path.join(dir_path, "../../../fixtures/chunantes/functions/function0/function.zip"), "rb") as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, "application/zip", flength, None)
    file.seek(0)

    return file, file_filename


def get_description_function():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.md"
    f = BytesIO()
    with open(
        os.path.join(dir_path, "../../../fixtures/chunantes/functions/function3/description.md"), "rb"
    ) as desc_file:
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


def get_sample_function_metadata():
    return {
        "owner": "foo",
        "permissions": DEFAULT_PERMISSIONS,
        "description": DEFAULT_STORAGE_ADDRESS,
        "functionrithm": DEFAULT_STORAGE_ADDRESS,
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
