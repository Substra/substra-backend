import os
import uuid
import docker.errors
import traceback
import json
import re

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
