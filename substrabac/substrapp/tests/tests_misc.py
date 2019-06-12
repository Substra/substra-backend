from django.test import TestCase

from mock import patch
from substrapp.tasks.utils import get_cpu_sets, get_gpu_sets, ExceptionThread, \
    update_statistics

from substrapp.tests.common import JobStats, Stats, gpu

from substrapp.ledger_utils import LedgerNotFound, LedgerBadResponse

from substrapp.ledger_utils import get_object_from_ledger, log_fail_tuple, log_start_tuple, \
    log_success_tuple, query_tuples


class MockDevice():
    """A mock device to temporarily suppress output to stdout
    Similar to UNIX /dev/null.
    """

    def write(self, s):
        pass


class MiscTests(TestCase):
    """Misc tests"""

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

    def test_get_object_from_ledger(self):
        with patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = LedgerNotFound('Not Found')
            self.assertRaises(LedgerNotFound, get_object_from_ledger, 'pk', 'fake_query')

        with patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.side_effect = LedgerBadResponse('Bad Response')
            self.assertRaises(LedgerBadResponse, get_object_from_ledger, 'pk', 'fake_query')

        with patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = {'key': 'pk'}
            data = get_object_from_ledger('pk', 'good_query')
            self.assertEqual(data['key'], 'pk')

    def test_log_fail_tuple(self):
        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            log_fail_tuple('traintuple', 'pk', 'error_msg')

        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            log_fail_tuple('testtuple', 'pk', 'error_msg')

    def test_log_start_tuple(self):
        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            log_start_tuple('traintuple', 'pk')

        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            log_start_tuple('testtuple', 'pk')

    def test_log_success_tuple(self):
        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            res = {
                'end_model_file_hash': 'hash',
                'end_model_file': 'storageAddress',
                'global_perf': '0.99',
                'job_task_log': 'log',
            }
            log_success_tuple('traintuple', 'pk', res)

        with patch('substrapp.ledger_utils.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = None
            res = {
                'global_perf': '0.99',
                'job_task_log': 'log',
            }
            log_success_tuple('testtuple', 'pk', res)

    def test_query_tuples(self):
        with patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = None
            query_tuples('traintuple', 'data_owner')

        with patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = None
            query_tuples('testtuple', 'data_owner')
