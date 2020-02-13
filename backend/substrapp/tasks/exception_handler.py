import os
import uuid
import docker.errors
import traceback
import json
import re
import inspect


LANGUAGES = {
    'ShellScript': '00',
    'Python': '01'
}

SERVICES = {
    'System': '00',
    'Docker': '01'
}

EXCEPTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exceptions.json')

EXCEPTIONS_UUID_LENGTH = 7

if os.path.exists(EXCEPTION_PATH):
    try:
        EXCEPTIONS_MAP = json.load(open(EXCEPTION_PATH))
    except Exception:
        # The json may be corrupted
        EXCEPTIONS_MAP = dict()
else:
    EXCEPTIONS_MAP = dict()


def get_exception_codes_from_docker_trace():
    container_code = EXCEPTIONS_MAP[docker.errors.ContainerError.__name__]

    # Get last line of the docker traceback which contains the traceback inside the container
    docker_traceback = traceback.format_exc().splitlines()[-1].encode('utf_8').decode('unicode_escape')
    docker_traceback = re.split(':| |\n', docker_traceback)

    exception_codes = [code for exception, code in EXCEPTIONS_MAP.items()
                       if exception in docker_traceback and code != container_code]

    return exception_codes


def get_exception_code(exception_type):

    service_code = SERVICES['System']
    exception_code = EXCEPTIONS_MAP.get(exception_type.__name__, '0000')    # '0000' is default exception code

    # Exception inside a docker container
    if docker.errors.ContainerError.__name__ in EXCEPTIONS_MAP and \
       exception_code == EXCEPTIONS_MAP[docker.errors.ContainerError.__name__]:

        exception_codes = get_exception_codes_from_docker_trace()

        if len(exception_codes) > 0:
            # Take the first code in the list (may have more if multiple exceptions are raised)
            service_code = SERVICES['Docker']
            exception_code = exception_codes.pop()

    return exception_code, service_code


def compute_error_code(exception):
    exception_uuid = str(uuid.uuid4())[:EXCEPTIONS_UUID_LENGTH]
    exception_code, service_code = get_exception_code(exception.__class__)
    error_code = f'[{service_code}-{LANGUAGES["Python"]}-{exception_code}-{exception_uuid}]'
    return error_code


def exception_tree(cls, exceptions_classes):
    exceptions_classes.add(cls.__name__)
    for subcls in cls.__subclasses__():
        exception_tree(subcls, exceptions_classes)


def find_exception(module):
    # Exception classes in module
    exceptions = [ename for ename, eclass in inspect.getmembers(module, inspect.isclass)
                  if issubclass(eclass, BaseException)]

    # Exception classes in submodule

    try:
        submodules = inspect.getmembers(module, inspect.ismodule)
    except Exception:
        submodules = []

    for submodule_name, submodule in submodules:
        try:
            classes = inspect.getmembers(submodule, inspect.isclass)
        except Exception:
            classes = []

        exceptions += [ename for ename, eclass in classes
                       if issubclass(eclass, BaseException)]

    return set(exceptions)


def generate_exceptions_map(append=True):

    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings.prod'

    import requests.exceptions
    import celery.exceptions
    import tarfile
    import django.core.exceptions
    import django.urls
    import django.utils
    import django.db
    import django.http
    import django.db.transaction
    import rest_framework.exceptions

    # Modules to inspect
    MODULES = [docker.errors, requests.exceptions, celery.exceptions, tarfile,   # noqa: N806
               django.core.exceptions, django.urls, django.db, django.http, django.db.transaction,
               django.utils, rest_framework.exceptions]

    exceptions_classes = set()

    # Add exceptions from modules
    for errors_module in MODULES:
        exceptions_classes.update(find_exception(errors_module))

    # Add exceptions from python
    exception_tree(BaseException, exceptions_classes)

    exceptions_classes = sorted(exceptions_classes)

    if os.path.exists(EXCEPTION_PATH) and append:
        # Append values to it
        json_exceptions = json.load(open(EXCEPTION_PATH))

        # get all new exceptions
        exceptions_classes = [e for e in exceptions_classes if e not in json_exceptions.keys()]

        # get the last value
        start_value = max(map(int, json_exceptions.values()))

        for code_exception, exception_name in enumerate(exceptions_classes, start=start_value + 1):
            json_exceptions[exception_name] = f'{code_exception:04d}'

        return json_exceptions

    else:
        # Generate the json exceptions
        json_exceptions = dict()
        for code_exception, exception_name in enumerate(exceptions_classes, start=1):
            json_exceptions[exception_name] = f'{code_exception:04d}'

        return json_exceptions


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings.common'
    json_exceptions = generate_exceptions_map()
    with open(EXCEPTION_PATH, 'w') as outfile:
        json.dump(json_exceptions, outfile, indent=4)
