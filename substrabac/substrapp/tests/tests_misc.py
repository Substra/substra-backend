from django.test import TestCase, override_settings
from django.core.management import call_command
from rest_framework import status

import json
import os
import sys
from io import StringIO
import shutil
from mock import patch
from substrapp.job_utils import get_cpu_sets, get_gpu_sets, ExceptionThread, update_statistics


from substrapp.models import Dataset
from substrapp.serializers import LedgerDataSerializer

MEDIA_ROOT = "/tmp/unittests_misc/"


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


class MockDevice():
    """A mock device to temporarily suppress output to stdout
    Similar to UNIX /dev/null.
    """

    def write(self, s):
        pass


class MiscTests(TestCase):
    """Misc tests"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_cpu_sets(self):
        cpu_count = 16
        for concurrency in range(1, cpu_count + 1, 1):
            self.assertEqual(concurrency, len(get_cpu_sets(cpu_count, concurrency)))

    def test_gpu_sets(self):
        gpu_list = ['0', '1']
        for concurrency in range(1, len(gpu_list) + 1, 1):
            self.assertEqual(concurrency, len(get_gpu_sets(gpu_list, concurrency)))

        self.assertFalse(get_gpu_sets([], concurrency))

    def test_exception_thread(self):

        training = ExceptionThread(target=lambda x, y: x / y,
                                   args=(3, 0),
                                   daemon=True)

        with patch('sys.stderr', new=MockDevice()):
            training.start()
            training.join()

        self.assertTrue(hasattr(training, '_exception'))
        with self.assertRaises(ZeroDivisionError):
            raise training._exception

    def test_update_statistics(self):

        # Statistics

        job_statistics = JobStats.get_new_stats()
        tmp_statistics = JobStats.get_new_stats()

        update_statistics(job_statistics, None, None)
        self.assertEqual(tmp_statistics, job_statistics)

        update_statistics(job_statistics, None, [gpu()])
        self.assertNotEqual(tmp_statistics, job_statistics)
        self.assertEqual(job_statistics['gpu']['max'], 80)
        self.assertEqual(job_statistics['gpu_memory']['max'], 1)

        job_statistics = JobStats.get_new_stats()
        tmp_statistics = JobStats.get_new_stats()
        update_statistics(job_statistics, Stats.get_stats(), None)
        self.assertNotEqual(tmp_statistics, job_statistics)
        self.assertNotEqual(job_statistics['memory']['max'], 0)
        self.assertNotEqual(job_statistics['cpu']['max'], 0)
        self.assertNotEqual(job_statistics['netio']['rx'], 0)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class CommandsTestCase(TestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_bulkcreatedata(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.join(dir_path, '../../fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip')
        data_path2 = os.path.join(dir_path, '../../fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip')

        data = {'files': [data_path1, data_path2],
                'dataset_keys': ['bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af'],
                'test_only': False}

        pkhash1 = '62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a'
        pkhash2 = '42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9'

        class FakeFilter(object):
            def __init__(self, count):
                self.count_value = count

            def count(self):
                return self.count_value

        with patch.object(Dataset.objects, 'filter') as mdataset, \
                patch.object(LedgerDataSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1, pkhash2],
                                    'validated': True},
                                    status.HTTP_201_CREATED)
            mdataset.return_value = FakeFilter(1)
            saved_stdout = sys.stdout

            out_data = [
                {
                    "pkhash": "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                    "file": "/media/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip",
                    "validated": True
                },
                {
                    "pkhash": "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9",
                    "file": "/media/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip",
                    "validated": True
                }
            ]
            wanted_output = f'Succesfully added data via bulk with status code {status.HTTP_201_CREATED} and data: {json.dumps(out_data, indent=4)}'

            try:
                out = StringIO()
                sys.stdout = out
                call_command('bulkcreatedata', json.dumps(data))

                output = out.getvalue().strip()
                self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout
