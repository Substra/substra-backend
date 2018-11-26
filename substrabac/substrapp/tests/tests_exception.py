import os
import json
import docker
from django.test import TestCase
from substrapp.generate_exceptions_map import exception_tree, find_exception, MODULES
from substrapp.exception_handler import compute_error_code, get_exception_code


class MiscTests(TestCase):
    """Misc tests"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_exception_map(self):
        """Test if the exception map in exception.json is complete"""

        exceptions_classes = set()
        for errors_module in MODULES:
            exceptions_classes.update(find_exception(errors_module))
        exception_tree(BaseException, exceptions_classes)
        json_exceptions_build = dict()
        for code_exception, exception_name in enumerate(exceptions_classes, start=1):
            json_exceptions_build[exception_name] = '%04d' % code_exception

        EXCEPTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exceptions.json')

        json_exceptions = json.load(open(EXCEPTION_PATH))

        self.assertTrue(set(json_exceptions.keys()).issubset(set(json_exceptions_build.keys())))

    def test_exception_handler(self):

        try:
            1 / 0
        except Exception as e:
            error_code = compute_error_code(e)
            value_error_code, _ = get_exception_code(ZeroDivisionError)
            self.assertIn("00-01-%s" % value_error_code, error_code)

        client = docker.from_env()

        try:
            client.containers.run("python:3.6", ['python3', '-c', 'print(KO)'], remove=True)
        except Exception as e:
            error_code = compute_error_code(e)
            container_error_code, _ = get_exception_code(NameError)
            self.assertIn("01-01-%s" % container_error_code, error_code)
