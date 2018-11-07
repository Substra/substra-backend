import os
import shutil
import tempfile

import mock
import time

from django.urls import reverse
from django.test import override_settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.utils import compute_hash
from substrapp.tasks import create_directory, get_computed_hash, get_remote_file, RessourceManager, monitoring_job, \
    save_challenge, save_challenge_from_local, untar_algo, untar_algo_from_local, get_hash

from .common import get_sample_challenge, get_sample_dataset, get_sample_data, get_sample_script

import tarfile
from threading import Thread
from .tests_misc import Stats
MEDIA_ROOT = tempfile.mkdtemp()


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class QueryTests(APITestCase):

    def setUp(self):
        self.challenge_description, self.challenge_description_filename, \
            self.challenge_metrics, self.challenge_metrics_filename = get_sample_challenge()
        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_data()
        self.data_description, self.data_description_filename, self.data_data_opener, self.data_opener_filename = get_sample_dataset()

        self.RessourceManager = RessourceManager()


    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
            os.remove('./sample_metrics.py')
            os.remove('./sample.tar.gz')
        except FileNotFoundError:
            pass

    def test_create_directory(self):
        directory = './test/'
        create_directory(directory)
        self.assertTrue(os.path.exists(directory))
        shutil.rmtree(directory)

    def test_get_computed_hash(self):
        with mock.patch('substrapp.tasks.requests.get') as mocked_function:
            mocked_function.return_value = HttpResponse(str(self.script.read()))
            _, pkhash = get_computed_hash('test')
            self.assertEqual(pkhash, 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02')

        with mock.patch('substrapp.tasks.requests.get') as mocked_function:
            response = HttpResponse()
            response.status_code = status.HTTP_400_BAD_REQUEST
            mocked_function.return_value = response
            self.assertRaises(Exception, get_computed_hash, ('test', ))

    def test_get_remote_file(self):
        obj = {'storageAddress': 'test',
               'hash': 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02'}

        with mock.patch('substrapp.tasks.get_computed_hash') as mocked_function:
            content = str(self.script.read())
            pkhash = compute_hash(content)
            mocked_function.return_value = content, pkhash
            content_remote, pkhash_remote = get_remote_file(obj)
            self.assertEqual(pkhash_remote, 'da920c804c4724f1ce7bd0484edcf4aafa209d5bd54e2e89972c087a487cbe02')
            self.assertEqual(content_remote, content)

        with mock.patch('substrapp.tasks.get_computed_hash') as mocked_function:
            content = str(self.script.read()) + ' FAIL'
            pkhash = compute_hash(content)
            mocked_function.return_value = content, pkhash
            self.assertRaises(Exception, get_remote_file, (obj, ))

    def test_Ressource_Manager(self):

        self.assertIn('M', self.RessourceManager.memory_limit_mb())

        cpu_set = self.RessourceManager.acquire_cpu_set()
        self.assertIn(cpu_set, self.RessourceManager._RessourceManager__used_cpu_sets)
        self.RessourceManager.return_cpu_set(cpu_set)
        self.assertNotIn(cpu_set, self.RessourceManager._RessourceManager__used_cpu_sets)

        gpu_set = self.RessourceManager.acquire_gpu_set()
        if gpu_set != 'no_gpu':
            self.assertIn(gpu_set, self.RessourceManager._RessourceManager__used_gpu_sets)
        self.RessourceManager.return_gpu_set(gpu_set)
        self.assertNotIn(gpu_set, self.RessourceManager._RessourceManager__used_gpu_sets)

    def test_monitoring_job(self):

        class FakeContainer(object):
            """docstring for FakeContainer"""
            def __init__(self):
                self.c_stats = Stats.get_stats()

            def stats(self, decode, stream):
                return self.c_stats

        class FakeClient(object):
            """docstring for FakeClient"""
            def __init__(self):
                self.containers = {'job': FakeContainer()}

        monitoring = Thread(target=monitoring_job, args=(FakeClient(), {'name': 'job'}))
        monitoring.start()
        time.sleep(0.1)
        monitoring.do_run = False
        monitoring.join()

        self.assertNotEqual(monitoring._stats['memory']['max'], 0)
        self.assertNotEqual(monitoring._stats['cpu']['max'], 0)
        self.assertNotEqual(monitoring._stats['netio']['rx'], 0)

    def test_save_challenge(self):

        with mock.patch('substrapp.tasks.get_remote_file') as mocked_function:
            content = str(self.script.read())
            pkhash = compute_hash(content)
            mocked_function.return_value = content.encode("utf-8"), pkhash
            save_challenge({'key': 'testkey', 'challenge': {'metrics': 'testmetrics'}})

        metric_path = os.path.join(MEDIA_ROOT, 'traintuple/testkey/metrics/metrics.py')
        self.assertTrue(os.path.exists(metric_path))

        class FakeMetric(object):
            """docstring for Metric"""
            def __init__(self):
                self.path = metric_path

        class FakeChallenge(object):
            """docstring for Challenge"""
            def __init__(self):
                self.metrics = FakeMetric()

        with mock.patch('substrapp.tasks.get_hash') as mocked_function:
            pkhash = compute_hash(content)
            mocked_function.return_value = pkhash
            os.makedirs(os.path.dirname(os.path.join(MEDIA_ROOT, 'traintuple/testkey2/metrics/')), exist_ok=True)
            save_challenge_from_local(FakeChallenge(), {'key': 'testkey2', 'challenge': {'metrics': {'hash': pkhash}}})

        self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'traintuple/testkey2/metrics/metrics.py')))

    def test_untar_algo(self):

        file = open('sample_metrics.py', 'w')
        file.write('Hello World')
        file.close()

        tf = tarfile.open('sample.tar.gz', mode='w:gz')
        tf.add('sample_metrics.py')
        tf.close()

        with mock.patch('substrapp.tasks.get_remote_file') as mocked_function:
            with open('sample.tar.gz', 'rb') as content:
                pkhash = get_hash('sample.tar.gz')
                mocked_function.return_value = content.read(), pkhash
                untar_algo({'key': 'testkey', 'algo': 'testalgo'})

        metric_path = os.path.join(MEDIA_ROOT, 'traintuple/testkey/sample_metrics.py')
        self.assertTrue(os.path.exists(metric_path))

        class FakeFile(object):
            """docstring for file"""
            def __init__(self):
                self.path = 'sample.tar.gz'
                self.name = 'sample.tar.gz'

        class FakeAlgo(object):
            """docstring for Challenge"""
            def __init__(self):
                self.file = FakeFile()

        with mock.patch('substrapp.tasks.get_hash') as mocked_function:
            pkhash = get_hash('sample.tar.gz')
            mocked_function.return_value = pkhash
            os.makedirs(os.path.dirname(os.path.join(MEDIA_ROOT, 'traintuple/testkey2/metrics/')), exist_ok=True)
            untar_algo_from_local(FakeAlgo(), {'key': 'testkey2', 'algo': {'hash': pkhash}})

        self.assertTrue(os.path.exists(os.path.join(MEDIA_ROOT, 'traintuple/testkey2/sample_metrics.py')))
