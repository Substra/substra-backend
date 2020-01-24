import os
import shutil
import logging

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from ..common import FakeAsyncResult, AuthenticatedClient

MEDIA_ROOT = "/tmp/unittests_views/"


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class TaskViewTests(APITestCase):
    client_class = AuthenticatedClient

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

        self.logger.setLevel(self.previous_level)

    def test_task_retrieve(self):

        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:  # noqa: N806
            mAsyncResult.return_value = FakeAsyncResult(status='SUCCESS')
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_task_retrieve_fail(self):
        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:  # noqa: N806
            mAsyncResult.return_value = FakeAsyncResult()
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_retrieve_pending(self):
        url = reverse('substrapp:task-detail', kwargs={'pk': 'pk'})
        with mock.patch('substrapp.views.task.AsyncResult') as mAsyncResult:  # noqa: N806
            mAsyncResult.return_value = FakeAsyncResult(status='PENDING', successful=False)
            response = self.client.get(url, **self.extra)
            self.assertEqual(response.data['message'],
                             'Task is either waiting, does not exist in this context or has been removed after 24h')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
