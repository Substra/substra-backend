import mock

from rest_framework.test import APITestCase
from substrapp.ledger.api import get_object_from_ledger

from ..assets import objective
from ..common import AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


class ViewTests(APITestCase):
    client_class = AuthenticatedClient

    def test_utils_get_object_from_ledger(self):

        with mock.patch('substrapp.ledger.api.query_ledger') as mquery_ledger:
            mquery_ledger.return_value = objective
            data = get_object_from_ledger('mychannel', '', 'queryObjective')

            self.assertEqual(data, objective)
