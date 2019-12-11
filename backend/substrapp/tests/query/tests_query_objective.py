import os
import shutil
import tempfile

import mock


from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.models import Objective, DataManager
from substrapp.utils import get_hash, compute_hash

from ..common import get_sample_objective, get_sample_datamanager, \
    get_temporary_text_file, AuthenticatedClient, get_sample_objective_metadata

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
@override_settings(LEDGER_SYNC_ENABLED=True)
@override_settings(DEFAULT_DOMAIN='http://testserver')
class ObjectiveQueryTests(APITestCase):
    client_class = AuthenticatedClient

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
        DataManager.objects.create(name='slide opener',
                                   description=self.data_description,
                                   data_opener=self.data_data_opener)

    def get_default_objective_data(self):

        self.objective_description, self.objective_description_filename, \
            self.objective_metrics, self.objective_metrics_filename = get_sample_objective()

        expected_hash = get_hash(self.objective_description)
        data = {
            'name': 'tough objective',
            'test_data_manager_key': get_hash(self.data_data_opener),
            'test_data_sample_keys': self.test_data_sample_keys,
            'description': self.objective_description,
            'metrics': self.objective_metrics,
            'permissions_public': True,
            'permissions_authorized_ids': [],
            'metrics_name': 'accuracy'
        }
        return expected_hash, data

    def test_add_objective_sync_ok(self):
        self.add_default_data_manager()
        pkhash, data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')
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
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_description_filename}')
            self.assertEqual(r['metrics'],
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_metrics_filename}')
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
        pkhash, data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        with mock.patch('substrapp.ledger.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {
                'message': 'Objective added in local db waiting for validation.'
                           'The substra network has been notified for adding this Objective'
            }
            response = self.client.post(url, data, format='multipart', **extra)

            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(r['validated'], False)
            self.assertEqual(r['description'],
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_description_filename}')
            self.assertEqual(r['metrics'],
                             f'http://testserver/media/objectives/{r["pkhash"]}/{self.objective_metrics_filename}')
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_add_objective_conflict(self):
        self.add_default_data_manager()

        pkhash, data = self.get_default_objective_data()

        url = reverse('substrapp:objective-list')

        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }

        with mock.patch('substrapp.ledger.invoke_ledger') as minvoke_ledger:
            minvoke_ledger.return_value = {'pkhash': pkhash}

            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(r['pkhash'], pkhash)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # XXX reload data as the previous call to post change it
            _, data = self.get_default_objective_data()
            response = self.client.post(url, data, format='multipart', **extra)
            r = response.json()

            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
            self.assertEqual(r['pkhash'], pkhash)

    def test_add_objective_ko(self):
        url = reverse('substrapp:objective-list')

        data = {'name': 'empty objective'}
        extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0',
        }
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'metrics': self.objective_metrics,
                'description': self.objective_description}
        response = self.client.post(url, data, format='multipart', **extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_objective_no_version(self):
        url = reverse('substrapp:objective-list')

        description_content = 'My Super top objective'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content,
                                              'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough objective',
            'test_data_sample_keys': self.test_data_sample_keys,
            'description': description,
            'metrics': metrics,
        }

        response = self.client.post(url, data, format='multipart')
        r = response.json()

        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_objective_wrong_version(self):
        url = reverse('substrapp:objective-list')

        description_content = 'My Super top objective'
        metrics_content = 'def metrics():\n\tpass'

        description = get_temporary_text_file(description_content,
                                              'description.md')
        metrics = get_temporary_text_file(metrics_content, 'metrics.py')

        data = {
            'name': 'tough objective',
            'test_data_sample_keys': self.test_data_sample_keys,
            'description': description,
            'metrics': metrics,
        }

        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }

        response = self.client.post(url, data, format='multipart', **extra)
        r = response.json()

        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_objective_metrics(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)

        with mock.patch('substrapp.views.utils.get_owner', return_value='foo'), \
                mock.patch('substrapp.views.utils.get_object_from_ledger') \
                as mget_object_from_ledger:
            mget_object_from_ledger.return_value = get_sample_objective_metadata()
            extra = {
                'HTTP_ACCEPT': 'application/json;version=0.0',
            }
            response = self.client.get(
                f'/objective/{objective.pkhash}/metrics/', **extra)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotEqual(objective.pkhash,
                                compute_hash(response.getvalue()))
            self.assertEqual(self.objective_metrics_filename,
                             response.filename)

    def test_get_objective_metrics_no_version(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)
        response = self.client.get(f'/objective/{objective.pkhash}/metrics/')
        r = response.json()
        self.assertEqual(r, {'detail': 'A version is required.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_objective_metrics_wrong_version(self):
        objective = Objective.objects.create(
            description=self.objective_description,
            metrics=self.objective_metrics)
        extra = {
            'HTTP_ACCEPT': 'application/json;version=-1.0',
        }
        response = self.client.get(f'/objective/{objective.pkhash}/metrics/',
                                   **extra)
        r = response.json()
        self.assertEqual(r, {'detail': 'Invalid version in "Accept" header.'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
