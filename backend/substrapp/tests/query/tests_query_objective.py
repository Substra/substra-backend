import os
import shutil
import tempfile
import json

import mock


from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective, DataManager

from ..common import get_sample_objective, get_sample_datamanager, \
    AuthenticatedClient, get_sample_objective_metadata

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DEFAULT_DOMAIN='http://testserver')
class ObjectiveQueryTests(APITestCase):
    client_class = AuthenticatedClient
    data_manager_pkhash = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

        self.test_data_sample_keys = [
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379',
            '5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389']

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_data_manager(self):
        dm = DataManager.objects.create(name='slide opener',
                                        description=self.data_description,
                                        data_opener=self.data_data_opener)
        self.data_manager_pkhash = dm.pkhash

    def get_default_objective_data(self):

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        return {
            'description': self.objective_description,
            'metrics': self.objective_metrics,
            'json': json.dumps({
                'name': 'tough objective',
                'test_data_manager_key': self.data_manager_pkhash,
                'test_data_sample_keys': self.test_data_sample_keys,
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
                'metrics_name': 'accuracy'
            }),
        }

    def test_add_objective_sync_ok(self):
        self.add_default_data_manager()
        data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {'pkhash': 'some key'}

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertIsNotNone(r['key'])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_objective_no_sync_ok(self):
        self.add_default_data_manager()
        data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {
                'message': 'Objective added in local db waiting for validation.'
                           'The substra network has been notified for adding this Objective'
            }
            response = self.client.post(url, data, format='multipart', **extra)

            r = response.json()

            self.assertIsNotNone(r['key'])
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_objective_ko(self):
        url = reverse('substrapp:objective-list')

        data = {'name': 'empty objective'}
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.objective_metrics,
                'description': self.objective_description}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_objective_metrics(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_objective_metadata()
            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(
                f'/objective/{objective.pkhash}/metrics/', **extra)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(self.objective_metrics_filename,
                             response.filename)
