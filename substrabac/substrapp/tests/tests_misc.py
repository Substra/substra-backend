from django.test import TestCase
from mock import patch
from substrapp.utils import get_cpu_sets, get_gpu_sets, ExceptionThread, update_statistics


class gpu():
    """Fake gpu"""
    def __init__(self):
        self.load = 0.8
        self.memoryUsed = 1024


class Stats():
    @classmethod
    def get_stats(cls):
        """ Docker stats"""
        return {'read': '2018-11-05T13:44:07.1782391Z', 'preread': '2018-11-05T13:44:06.1746531Z', 'pids_stats': {'current': 8}, 'blkio_stats': {'io_service_bytes_recursive': [{'major': 8, 'minor': 0, 'op': 'Read', 'value': 11776000}, {'major': 8, 'minor': 0, 'op': 'Write', 'value': 0}, {'major': 8, 'minor': 0, 'op': 'Sync', 'value': 0}, {'major': 8, 'minor': 0, 'op': 'Async', 'value': 11776000}, {'major': 8, 'minor': 0, 'op': 'Total', 'value': 11776000}], 'io_serviced_recursive': [{'major': 8, 'minor': 0, 'op': 'Read', 'value': 403}, {'major': 8, 'minor': 0, 'op': 'Write', 'value': 0}, {'major': 8, 'minor': 0, 'op': 'Sync', 'value': 0}, {'major': 8, 'minor': 0, 'op': 'Async', 'value': 403}, {'major': 8, 'minor': 0, 'op': 'Total', 'value': 403}], 'io_queue_recursive': [], 'io_service_time_recursive': [], 'io_wait_time_recursive': [], 'io_merged_recursive': [], 'io_time_recursive': [], 'sectors_recursive': []}, 'num_procs': 0, 'storage_stats': {}, 'cpu_stats': {'cpu_usage': {'total_usage': 22900421851, 'percpu_usage': [4944824970, 4964929089, 8163433379, 4827234413, 0, 0, 0, 0], 'usage_in_kernelmode': 5520000000, 'usage_in_usermode': 17350000000}, 'system_cpu_usage': 185691120000000, 'online_cpus': 8, 'throttling_data': {'periods': 0, 'throttled_periods': 0, 'throttled_time': 0}}, 'precpu_stats': {'cpu_usage': {'total_usage': 18898246805, 'percpu_usage': [3938977859, 3966955357, 7165817747, 3826495842, 0, 0, 0, 0], 'usage_in_kernelmode': 5470000000, 'usage_in_usermode': 13390000000}, 'system_cpu_usage': 185683050000000, 'online_cpus': 8, 'throttling_data': {'periods': 0, 'throttled_periods': 0, 'throttled_time': 0}}, 'memory_stats': {'usage': 1404354560, 'max_usage': 1404616704, 'stats': {'active_anon': 1387876352, 'active_file': 708608, 'cache': 11849728, 'dirty': 241664, 'hierarchical_memory_limit': 8589934592, 'hierarchical_memsw_limit': 17179869184, 'inactive_anon': 0, 'inactive_file': 11141120, 'mapped_file': 4927488, 'pgfault': 341053, 'pgmajfault': 53, 'pgpgin': 343366, 'pgpgout': 1605, 'rss': 1388003328, 'rss_huge': 0, 'total_active_anon': 1387876352, 'total_active_file': 708608, 'total_cache': 11849728, 'total_dirty': 241664, 'total_inactive_anon': 0, 'total_inactive_file': 11141120, 'total_mapped_file': 4927488, 'total_pgfault': 341053, 'total_pgmajfault': 53, 'total_pgpgin': 343366, 'total_pgpgout': 1605, 'total_rss': 1388003328, 'total_rss_huge': 0, 'total_unevictable': 0, 'total_writeback': 0, 'unevictable': 0, 'writeback': 0}, 'limit': 8589934592}, 'name': '/job_c9868', 'id': '60fa7ab1c6dafdaa08ec3e2b95b16120757ac5cb7ebd512b3526b2d521623776', 'networks': {'eth0': {'rx_bytes': 758, 'rx_packets': 9, 'rx_errors': 0, 'rx_dropped': 0, 'tx_bytes': 0, 'tx_packets': 0, 'tx_errors': 0, 'tx_dropped': 0}}}


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
