import os
import shutil
import tempfile

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective, Model
from substrapp.utils import compute_hash, new_uuid
from node.authentication import NodeUser

from ..common import get_sample_objective, AuthenticatedClient, get_sample_model

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CompositeTraintupleQueryTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        self.train_data_sample_keys = ['5c1d9cd1-c2c1-082d-de09-21b56d11030c']
        self.fake_key = '5c1d9cd1-c2c1-082d-de09-21b56d11030c'

        self.model, _ = get_sample_model()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_add_compositetraintuple_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:composite_traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'compute_plan_id': self.fake_key,
            'in_head_model_key': self.fake_key,
            'in_trunk_model_key': self.fake_key,
            'out_trunk_model_permissions': {
                'public': False,
                'authorized_ids': ["Node-1", "Node-2"],
            },
        }

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.compositetraintuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = {'pkhash': key}

            response = self.client.post(url, data, format='json', **extra)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_traintuple_with_implicit_compute_plan(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:composite_traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'in_head_model_key': self.fake_key,
            'in_trunk_model_key': self.fake_key,
            'out_trunk_model_permissions': {
                'public': False,
                'authorized_ids': ["Node-1", "Node-2"],
            },
            # implicit compute plan
            'rank': 0,
            'compute_plan_id': None
        }
        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.create_computeplan') as mcreate_computeplan, \
                mock.patch('substrapp.ledger.assets.create_compositetraintuple') as mcreate_compositetraintuple:

            mcreate_computeplan.return_value = {'compute_plan_id': str(new_uuid())}
            mcreate_compositetraintuple.return_value = {'key': str(new_uuid())}

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(mcreate_computeplan.call_count, 1)
            self.assertEqual(mcreate_compositetraintuple.call_count, 1)

    @override_settings(LEDGER_SYNC_ENABLED=False)
    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory'
    )
    def test_add_compositetraintuple_no_sync_ok(self):
        # Add associated objective
        description, _, metrics, _ = get_sample_objective()
        Objective.objects.create(description=description,
                                 metrics=metrics)
        # post data
        url = reverse('substrapp:composite_traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'algo_key': self.fake_key,
            'data_manager_key': self.fake_key,
            'objective_key': self.fake_key,
            'compute_plan_id': self.fake_key,
            'in_head_model_key': self.fake_key,
            'in_trunk_model_key': self.fake_key,
            'out_trunk_model_permissions': {
                'public': False,
                'authorized_ids': ["Node-1", "Node-2"],
            },
        }

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.assets.invoke_ledger') as minvoke_ledger, \
                mock.patch('substrapp.views.compositetraintuple.query_ledger') as mquery_ledger:

            key = new_uuid()
            mquery_ledger.return_value = {'key': key}
            minvoke_ledger.return_value = None

            response = self.client.post(url, data, format='json', **extra)

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_compositetraintuple_ko(self):
        url = reverse('substrapp:composite_traintuple-list')

        data = {
            'train_data_sample_keys': self.train_data_sample_keys,
            'model_key': self.fake_key
        }

        extra = {
            'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()
        self.assertIn('This field may not be null.', r['algo_key'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        o = Objective.objects.create(description=self.objective_description,
                                     metrics=self.objective_metrics)
        data = {'objective': o.pkhash}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_head_model_ok(self):
        checksum = compute_hash(self.model.read(), key='key_traintuple')
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        permissions = {
            "process": {
                "public": False,
                "authorized_ids": ['substra']
            }
        }
        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger, \
                mock.patch('substrapp.views.model.type') as mtype:
            mget_object_from_ledger.return_value = permissions
            mtype.return_value = NodeUser
            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/model/{head_model.pkhash}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(head_model.checksum, compute_hash(response.getvalue(), key='key_traintuple'))

    def test_get_head_model_ko_user(self):
        checksum = compute_hash(self.model.read(), key='key_traintuple')
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        permissions = {
            "process": {
                "public": False,
                "authorized_ids": ['substra']
            }
        }
        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = permissions
            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/model/{head_model.pkhash}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_head_model_ko_wrong_node(self):
        checksum = compute_hash(self.model.read(), key='key_traintuple')
        head_model = Model.objects.create(file=self.model, checksum=checksum, validated=True)
        permissions = {
            "process": {
                "public": False,
                "authorized_ids": ['owkin']
            }
        }
        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger, \
                mock.patch('substrapp.views.model.type') as mtype:
            mget_object_from_ledger.return_value = permissions
            mtype.return_value = NodeUser

            extra = {
                'HTTP_SUBSTRA_CHANNEL_NAME': 'mychannel',
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(f'/model/{head_model.pkhash}/file/', **extra)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
