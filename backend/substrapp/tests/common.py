from http.cookies import SimpleCookie
from io import StringIO, BytesIO
import os
import base64

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.test import APIClient


# This function helper generate a basic authentication header with given credentials
# Given username and password it returns "Basic GENERATED_TOKEN"
from users.serializers import CustomTokenObtainPairSerializer


def generate_basic_auth_header(username, password):
    return 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()


def generate_jwt_auth_header(jwt):
    return 'JWT ' + jwt


class AuthenticatedClient(APIClient):

    def request(self, **kwargs):

        # create user
        username = 'substra'
        password = 'p@$swr0d44'
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
        # simulate login
        serializer = CustomTokenObtainPairSerializer(data={
            'username': username,
            'password': password
        })

        serializer.is_valid()
        data = serializer.validated_data
        access_token = str(data.access_token)

        # simulate right httpOnly cookie and Authorization jwt
        jwt_auth_header = generate_jwt_auth_header('.'.join(access_token.split('.')[0:2]))
        self.credentials(HTTP_AUTHORIZATION=jwt_auth_header)
        self.cookies = SimpleCookie({'signature': access_token.split('.')[2]})

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
    text_file = InMemoryUploadedFile(f, None, filename, 'text', flength, None)
    # Setting the file to its start
    text_file.seek(0)
    return text_file


def get_sample_objective():

    dir_path = os.path.dirname(os.path.realpath(__file__))

    description_content = "Super objective"
    description_filename = "description.md"
    description = get_temporary_text_file(description_content, description_filename)

    metrics_filename = "metrics.zip"
    f = BytesIO(b'')
    with open(os.path.join(dir_path,
                           '../../../fixtures/chunantes/objectives/objective0/metrics.zip'), 'rb') as zip_file:
        flength = f.write(zip_file.read())
    metrics = InMemoryUploadedFile(f, None, metrics_filename,
                                   'application/zip', flength, None)
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
    f = BytesIO(b'foo')
    with open(os.path.join(dir_path, '../../../fixtures/owkin/datasamples/datasample4/0024900.zip'), 'rb') as zip_file:
        flength = f.write(zip_file.read())

    file = InMemoryUploadedFile(f, None, file_filename,
                                'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_zip_data_sample_2():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO(b'foo')
    with open(os.path.join(dir_path, '../../../fixtures/owkin/datasamples/test/0024901.zip'), 'rb') as zip_file:
        flength = f.write(zip_file.read())

    file = InMemoryUploadedFile(f, None, file_filename,
                                'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_tar_data_sample():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(os.path.join(
            dir_path, '../../../fixtures/owkin/datasamples/datasample4/0024900.tar.gz'), 'rb') as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, 'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_algo():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.tar.gz"
    f = BytesIO()
    with open(os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo3/algo.tar.gz'), 'rb') as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, 'application/tar+gzip', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_composite_algo():
    return get_sample_algo()


def get_sample_algo_zip():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.zip"
    f = BytesIO()
    with open(os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo0/algo.zip'), 'rb') as tar_file:
        flength = f.write(tar_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, 'application/zip', flength, None)
    file.seek(0)

    return file, file_filename


def get_description_algo():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_filename = "file.md"
    f = BytesIO()
    with open(os.path.join(dir_path, '../../../fixtures/chunantes/algos/algo3/description.md'), 'rb') as desc_file:
        flength = f.write(desc_file.read())

    file = InMemoryUploadedFile(f, None, file_filename, 'application/text', flength, None)
    file.seek(0)

    return file, file_filename


def get_sample_model():
    model_content = "0.1, 0.2, -1.0"
    model_filename = "model.bin"
    model = get_temporary_text_file(model_content, model_filename)

    return model, model_filename


DEFAULT_PERMISSIONS = {
    'process': {
        'public': True,
        'authorizedIDs': [],
    }
}


def get_sample_algo_metadata():
    return {
        'owner': 'foo',
        'permissions': DEFAULT_PERMISSIONS,
    }


def get_sample_objective_metadata():
    return {
        'owner': 'foo',
        'permissions': DEFAULT_PERMISSIONS,
    }


class FakeMetrics(object):
    def __init__(self, filepath='path'):
        self.path = filepath

    def save(self, p, f):
        return

    def read(self, *args, **kwargs):
        return b'foo'


class FakeObjective(object):
    def __init__(self, filepath='path'):
        self.metrics = FakeMetrics(filepath)


class FakeOpener(object):
    def __init__(self, filepath):
        self.path = filepath
        self.name = self.path


class FakeDataManager(object):
    def __init__(self, filepath):
        self.data_opener = FakeOpener(filepath)


class FakeFilterDataManager(object):
    def __init__(self, count):
        self.count_value = count

    def count(self):
        return self.count_value


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
