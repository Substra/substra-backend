from django.test import TestCase

from mock import patch
from substrapp.task_utils import get_cpu_sets, get_gpu_sets, ExceptionThread, \
    update_statistics

from substrapp.tests.common import JobStats, Stats, gpu

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
            self.assertEqual(concurrency,
                             len(get_cpu_sets(cpu_count, concurrency)))

    def test_gpu_sets(self):
        gpu_list = ['0', '1']
        for concurrency in range(1, len(gpu_list) + 1, 1):
            self.assertEqual(concurrency,
                             len(get_gpu_sets(gpu_list, concurrency)))

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
