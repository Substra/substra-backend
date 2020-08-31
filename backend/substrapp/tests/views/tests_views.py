import mock

from rest_framework.test import APITestCase

from substrapp.views.datasample import path_leaf
from substrapp.ledger_utils import get_object_from_ledger


from ..assets import objective
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


class ViewTests(APITestCase):
    client_class = AuthenticatedClient

    def test_data_sample_path_view(self):
        self.assertEqual('tutu', path_leaf('/toto/tata/tutu'))
        self.assertEqual('toto', path_leaf('/toto/'))

    def test_utils_get_object_from_ledger(self):

        with mock.patch('substrapp.ledger_utils.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective
            data = get_object_from_ledger('mychannel', '', 'queryObjective')

            self.assertEqual(data, objective)
