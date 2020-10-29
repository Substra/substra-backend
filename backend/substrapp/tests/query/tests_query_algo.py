import os
import shutil
import tempfile
import json
import mock
import uuid

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective, Algo
from substrapp.serializers import LedgerAlgoSerializer
from substrapp.utils import compute_hash
from substrapp.ledger.exceptions import LedgerError

from ..common import get_sample_objective, get_sample_datamanager, \
    get_sample_algo, get_sample_algo_zip, AuthenticatedClient, \
    get_sample_algo_metadata

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(DEFAULT_DOMAIN='http://testserver')
class AlgoQueryTests(APITestCase):
    client_class = AuthenticatedClient
    objective_key = None

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.algo, self.algo_filename = get_sample_algo()
        self.algo_zip, self.algo_filename_zip = get_sample_algo_zip()

        self.data_description, self.data_description_filename, self.data_data_opener, \
            self.data_opener_filename = get_sample_datamanager()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def add_default_objective(self):
        o = Objective.objects.create(description=self.objective_description,
                                     metrics=self.objective_metrics)
        self.objective_key = str(o.key)

    def get_default_algo_data(self):
        return {
            'file': self.algo,
            'description': self.data_description,  # fake it
            'json': json.dumps({
                'name': 'super top algo',
                'objective_key': self.objective_key,
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            }),
        }

    def get_default_algo_data_zip(self):
        return {
            'file': self.algo_zip,
            'description': self.data_description,  # fake it
            'json': json.dumps({
                'name': 'super top algo',
                'objective_key': self.objective_key,
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            })
        }

    def test_add_algo_sync_ok(self):
        self.add_default_objective()
        data = self.get_default_algo_data_zip()

        url = reverse('substrapp:algo-list')
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {'key': 'some key'}

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
    def test_add_algo_no_sync_ok(self):
        self.add_default_objective()
        data = self.get_default_algo_data()

        url = reverse('substrapp:algo-list')
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {
                'message': 'Algo added in local db waiting for validation.'
                           'The substra network has been notified for adding this Algo'
            }
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertIsNotNone(r['key'])
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_algo_ko(self):
        url = reverse('substrapp:algo-list')

        # non existing associated objective
        data = {
            'file': self.algo,
            'description': self.data_description,
            'json': json.dumps({
                'name': 'super top algo',
                'objective_key': str(uuid.uuid4()),
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            }),
        }
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch.object(LedgerAlgoSerializer, 'create') as mcreate:
            mcreate.side_effect = LedgerError('Fail to add algo. Objective does not exist')

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()
            self.assertIn('does not exist', r['message'])
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            Objective.objects.create(description=self.objective_description,
                                     metrics=self.objective_metrics)

            # missing local storage field
            data = {
                'name': 'super top algo',
                'objective_key': self.objective_key,
                'permissions': {
                    'public': True,
                    'authorized_ids': [],
                },
            }
            response = self.client.post(url, data, format='json', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # missing ledger field
            data = {
                'file': self.algo,
                'description': self.data_description,
                'json': json.dumps({
                    'objective_key': self.objective_key,
                })
            }
            response = self.client.post(url, data, format='multipart', **extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_algo_files(self):
        algo = Algo.objects.create(file=self.algo)
        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_algo_metadata()

            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/algo/{algo.key}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(algo.checksum, compute_hash(response.getvalue()))
