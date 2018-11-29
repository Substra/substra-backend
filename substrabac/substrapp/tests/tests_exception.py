import os
import json
import docker
from django.test import TestCase
from substrapp.generate_exceptions_map import exception_tree, find_exception, MODULES
from substrapp.exception_handler import compute_error_code, get_exception_code


class ExceptionTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_exception_map(self):

        # Build the exception map from local configuration
        exceptions_classes = set()

        # Get exceptions of modules
        for errors_module in MODULES:
            exceptions_classes.update(find_exception(errors_module))

        # Get exceptions from python
        exception_tree(BaseException, exceptions_classes)

        # Build the exception map
        exception_map = dict()
        for code_exception, exception_name in enumerate(exceptions_classes, start=1):
            exception_map[exception_name] = '%04d' % code_exception

        # Exception map reference
        EXCEPTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exceptions.json')
        reference_exception_map = json.load(open(EXCEPTION_PATH))

        self.assertTrue(set(reference_exception_map.keys()).issubset(set(exception_map.keys())))

    def test_exception_handler(self):

        # Python exception in system
        try:
            1 / 0
        except Exception as e:
            error_code = compute_error_code(e)
            value_error_code, _ = get_exception_code(ZeroDivisionError)
            self.assertIn("00-01-%s" % value_error_code, error_code)

        # Python exception in docker
        try:
            client = docker.from_env()
            client.containers.run("python:3.6", ['python3', '-c', 'print(KO)'], remove=True)
        except Exception as e:
            error_code = compute_error_code(e)
            container_error_code, _ = get_exception_code(NameError)
            self.assertIn("01-01-%s" % container_error_code, error_code)
