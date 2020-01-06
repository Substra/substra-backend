import os
import shutil
import tempfile

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase


from substrapp.utils import get_hash

from ..common import get_sample_datamanager, AuthenticatedClient

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
@override_settings(DEFAULT_DOMAIN='http://testserver')
class DataManagerQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def get_default_datamanager_data(self):
        expected_hash = get_hash(self.data_data_opener)
        data = {
            'name': 'slide opener',
            'type': 'images',
            'permissions_public': True,
            'permissions_authorized_ids': [],
            'objective_key': '',
            'description': self.data_description,
            'data_opener': self.data_data_opener
        }
        return expected_hash, data

    def test_add_datamanager_sync_ok(self):

        pkhash, data = self.get_default_datamanager_data()

        url = reverse('substrapp:data_manager-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {'pkhash': pkhash}

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(r['validated'], True)
            self.assertEqual(r['description'],
                             f'http://testserver/media/datamanagers/{r["pkhash"]}/{self.data_description_filename}')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_datamanager_no_sync_ok(self):

        pkhash, data = self.get_default_datamanager_data()

        url = reverse('substrapp:data_manager-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {
                'message': 'DataManager added in local db waiting for validation.'
                           'The substra network has been notified for adding this DataManager'
            }
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(r['validated'], False)
            self.assertEqual(r['description'],
                             f'http://testserver/media/datamanagers/{r["pkhash"]}/{self.data_description_filename}')
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_datamanager_ko(self):
        data = {'name': 'toto'}

        url = reverse('substrapp:data_manager-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_datamanager_no_version(self):

        _, data = self.get_default_datamanager_data()

        url = reverse('substrapp:data_manager-list')

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_datamanager_wrong_version(self):

        _, data = self.get_default_datamanager_data()

        url = reverse('substrapp:data_manager-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
