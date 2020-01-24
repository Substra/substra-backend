import os
import json
import docker
from django.test import TestCase
from substrapp.tasks.exception_handler import compute_error_code, get_exception_code, generate_exceptions_map


class ExceptionTests(TestCase):

    def test_exception_map(self):

        # Build the exception map
        exception_map = generate_exceptions_map(append=False)
        # Exception map reference
        exception_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tasks/exceptions.json')
        reference_exception_map = json.load(open(exception_path))

        self.assertTrue(set(reference_exception_map.keys()).issubset(set(exception_map.keys())))

    def test_exception_handler(self):

        # Python exception in system
        try:
            1 / 0
        except Exception as e:
            error_code = compute_error_code(e)
            value_error_code, _ = get_exception_code(ZeroDivisionError)
            self.assertIn(f'00-01-{value_error_code}', error_code)

        # Python exception in docker
        try:
            client = docker.from_env()
            client.containers.run("python:3.6", ['python3', '-c', 'print(KO)'], remove=True)
        except Exception as e:
            error_code = compute_error_code(e)
            container_error_code, _ = get_exception_code(NameError)
            self.assertIn(f'01-01-{container_error_code}', error_code)
