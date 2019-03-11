from io import StringIO, BytesIO
import os

from django.core.files.uploadedfile import InMemoryUploadedFile
from .tests_misc import Stats


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
    text_file = InMemoryUploadedFile(f, None, filename, 'text', flength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


def get_sample_challenge():
    description_content = "Super challenge"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    metrics_content = "def metrics():\n\tpass"
    metrics_filename = "metrics.py"
    metrics = get_temporary_text_file(metrics_content, metrics_filename)

    return description, description_filename, metrics, metrics_filename


def get_sample_script():
    script_content = "import slidelib\n\ndef read():\n\tpass"
    script_filename = "script.py"
    script = get_temporary_text_file(script_content, script_filename)

    return script, script_filename


def get_sample_dataset():
    description_content = "description"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_dataset2():
    description_content = "description 2"
    description_filename = "description2.md"
    description = get_temporary_text_file(description_content, description_filename)
    data_opener_content = "import os\nimport slidelib\n\ndef read():\n\tpass"
    data_opener_filename = "data_opener2.py"
    data_opener = get_temporary_text_file(data_opener_content, data_opener_filename)

    return description, description_filename, data_opener, data_opener_filename


def get_sample_data():
    file_content = "0\n1\n2"
    file_filename = "file.csv"
    file = get_temporary_text_file(file_content, file_filename)

    return file, file_filename


def get_sample_zip_data():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO(b'foo')
    with open(os.path.join(dir_path, '../../fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip'), 'rb') as zip_file:
        flength = f.write(zip_file.read())

    file = InMemoryUploadedFile(f, None, file_filename,
                                'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_tar_data():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(os.path.join(dir_path, '../../fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.tar.gz'), 'rb') as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename,
                                'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_algo():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(os.path.join(dir_path, '../../fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/algo.tar.gz'), 'rb') as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename,
                                'application/tar+gzip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_model():
    model_content = "0.1, 0.2, -1.0"
    model_filename = "model.bin"
    model = get_temporary_text_file(model_content, model_filename)

    return model, model_filename


class FakeContainer(object):
    def __init__(self):
        self.c_stats = Stats.get_stats()

    def stats(self, decode, stream):
        return self.c_stats


class FakeClient(object):
    def __init__(self):
        self.containers = {'job': FakeContainer()}


class FakeMetrics(object):
    def __init__(self, filepath='path'):
        self.path = filepath

    def save(self, p, f):
        return


class FakeChallenge(object):
    def __init__(self, filepath='path'):
        self.metrics = FakeMetrics(filepath)


class FakeOpener(object):
    def __init__(self, filepath):
        self.path = filepath
        self.name = self.path


class FakeDataset(object):
    def __init__(self, filepath):
        self.data_opener = FakeOpener(filepath)


class FakeFilterDataset(object):
    def __init__(self, count):
        self.count_value = count

    def count(self):
        return self.count_value


class FakeFile(object):
    def __init__(self, filepath):
        self.path = filepath
        self.name = self.path


class FakeData(object):
    def __init__(self, filepath):
        self.file = FakeFile(filepath)


class FakePath(object):
    def __init__(self, filepath):
        self.path = filepath


class FakeModel(object):
    def __init__(self, filepath):
        self.file = FakePath(filepath)


class FakeAsyncResult(object):
    def __init__(self, status=None, successful=True):
        if status is not None:
            self.status = status
        self.success = successful
        self.result = {'res': 'result'}

    def successful(self):
        return self.success


class FakeRequest(object):
    def __init__(self, status, content):
        self.status_code = status
        self.content = content


class FakeTask(object):
    def __init__(self, task_id):
        self.id = task_id
