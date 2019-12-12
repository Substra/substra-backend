from django.test import TestCase

from mock import patch
from substrapp.tasks.utils import get_cpu_sets, get_gpu_sets

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
        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_fail_tuple('traintuple', 'pk', 'error_msg')

        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_fail_tuple('testtuple', 'pk', 'error_msg')

    def test_log_start_tuple(self):
        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_start_tuple('traintuple', 'pk')

        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            log_start_tuple('testtuple', 'pk')

    def test_log_success_tuple(self):
        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
            res = {
                'end_model_file_hash': 'hash',
                'end_model_file': 'storageAddress',
                'job_task_log': 'log',
            }
            log_success_tuple('traintuple', 'pk', res)

        with patch('substrapp.ledger_utils.update_ledger') as mupdate_ledger:
            mupdate_ledger.return_value = None
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
