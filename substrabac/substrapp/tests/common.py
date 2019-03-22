from io import StringIO, BytesIO
import os

from django.core.files.uploadedfile import InMemoryUploadedFile

class gpu():
    """Fake gpu"""

    def __init__(self):
        self.load = 0.8
        self.memoryUsed = 1024


class Stats():
    @classmethod
    def get_stats(cls):
        """ Docker stats"""
        return {"read": "2018-11-05T13:44:07.1782391Z",
                "preread": "2018-11-05T13:44:06.1746531Z",
                "pids_stats": {
                    "current": 8
                },
                "num_procs": 0,
                "storage_stats": {},
                "cpu_stats": {
                    "cpu_usage": {
                        "total_usage": 22900421851,
                        "percpu_usage": [
                            4944824970,
                            4964929089,
                            8163433379,
                            4827234413,
                            0,
                            0,
                            0,
                            0
                        ],
                        "usage_in_kernelmode": 5520000000,
                        "usage_in_usermode": 17350000000
                    },
                    "system_cpu_usage": 185691120000000,
                    "online_cpus": 8,
                    "throttling_data": {
                        "periods": 0,
                        "throttled_periods": 0,
                        "throttled_time": 0
                    }},
                "precpu_stats": {
                    "cpu_usage": {
                        "total_usage": 18898246805,
                        "percpu_usage": [
                            3938977859,
                            3966955357,
                            7165817747,
                            3826495842,
                            0,
                            0,
                            0,
                            0
                        ],
                        "usage_in_kernelmode": 5470000000,
                        "usage_in_usermode": 13390000000
                    },
                    "system_cpu_usage": 185683050000000,
                    "online_cpus": 8,
                    "throttling_data": {
                        "periods": 0,
                        "throttled_periods": 0,
                        "throttled_time": 0
                    }
                },
                "memory_stats": {
                    "usage": 1404354560,
                    "max_usage": 1404616704,
                    "limit": 8589934592
                },
                "name": "/job_c9868",
                "id": "60fa7ab1c6dafdaa08ec3e2b95b16120757ac5cb7ebd512b3526b2d521623776",
                "networks": {
                    "eth0": {
                        "rx_bytes": 758,
                        "rx_packets": 9,
                        "rx_errors": 0,
                        "rx_dropped": 0,
                        "tx_bytes": 0,
                        "tx_packets": 0,
                        "tx_errors": 0,
                        "tx_dropped": 0
                    }
                }}


class JobStats():

    @classmethod
    def get_new_stats(cls):
        return {'memory': {'max': 0,
                           'current': [0]},
                'gpu_memory': {'max': 0,
                               'current': [0]},
                'cpu': {'max': 0,
                        'current': [0]},
                'gpu': {'max': 0,
                        'current': []},
                'io': {'max': 0,
                       'current': []},
                'netio': {'rx': 0,
                          'tx': 0},
                'time': 0}


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

def get_sample_zip_data_2():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO(b'foo')
    with open(os.path.join(dir_path, '../../fixtures/owkin/data/test/0024901.zip'), 'rb') as zip_file:
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
        self.path = filepath


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
