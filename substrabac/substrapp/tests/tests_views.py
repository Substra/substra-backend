import os
import shutil
import tempfile

import mock

from django.urls import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from substrapp.views import DatasetViewSet, TrainTupleViewSet, ChallengeViewSet, AlgoViewSet
from substrapp.views.utils import JsonException, ComputeHashMixin
from substrapp.views.data import path_leaf
from substrapp.utils import compute_hash

from substrapp.models import Challenge, Dataset, Algo

from .common import get_sample_challenge, get_sample_dataset, get_sample_data, get_sample_script

MEDIA_ROOT = tempfile.mkdtemp()


challenge = [
    {
        "descriptionStorageAddress": "http://testserver/challenge/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/description/",
        "key": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
        "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
        "metrics": {
            "hash": "0bc732c26bafdc41321c2bffd35b6835aa35f7371a4eb02994642c2c3a688f60",
            "name": "macro-average recall",
            "storageAddress": "http://testserver/challenge/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/metrics/"
        },
        "name": "Simplified skin lesion classification",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "testDataKeys": [
            "2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e",
            "533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1"
        ]
    },
    {
        "descriptionStorageAddress": "http://testserver/challenge/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description/",
        "key": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "dataset_key": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994",
        "metrics": {
            "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
            "name": "macro-average recall",
            "storageAddress": "http://testserver/challenge/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
        },
        "name": "Skin Lesion Classification Challenge",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "testDataKeys": [
            "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"
        ]
    }
]

model = [
    {
        "algo": {
            "hash": "6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f",
            "name": "Logistic regression",
            "storageAddress": "http://testserver/algo/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/file/"
        },
        "challenge": {
            "hash": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/challenge/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "creator": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "outModel": {
            "hash": "454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011",
            "storageAddress": "http://testserver/model/454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011/file/"
        },
        "key": "c164f4c714a78c7e2ba2016de231cdd41e3eac61289e08c1f711e74915a0868f",
        "log": "Train - CPU:75.04 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "permissions": "all",
        "startModel": None,
        "status": "done",
        "testData": {
            "keys": [
                "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"
            ],
            "openerHash": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
            "perf": 1,
            "worker": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1"
        },
        "trainData": {
            "keys": [
                "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
            ],
            "openerHash": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994",
            "perf": 1,
            "worker": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1"
        }
    }
]

data = [
    {
        "pkhash": "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
        "validated": True,
        "file": "http://localhost:8000/media/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip"
    },
    {
        "pkhash": "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9",
        "validated": True,
        "file": "http://localhost:8000/media/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip"
    },
    {
        "pkhash": "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1",
        "validated": True,
        "file": "http://localhost:8000/media/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip"
    },
    {
        "pkhash": "4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010",
        "validated": True,
        "file": "http://localhost:8000/media/data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip"
    },
    {
        "pkhash": "93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060",
        "validated": True,
        "file": "http://localhost:8000/media/data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip"
    },
    {
        "pkhash": "eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb",
        "validated": True,
        "file": "http://localhost:8000/media/data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip"
    },
    {
        "pkhash": "2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e",
        "validated": True,
        "file": "http://localhost:8000/media/data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip"
    },
    {
        "pkhash": "533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1",
        "validated": True,
        "file": "http://localhost:8000/media/data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip"
    }
]

dataset = [
    {
        "challengeKey": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
        "description": {
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/dataset/b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0/description/"
        },
        "key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
        "name": "Simplified ISIC 2018",
        "nbData": 6,
        "openerStorageAddress": "http://testserver/dataset/b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0/opener/",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "size": 1415097,
        "type": "Images"
    },
    {
        "challengeKey": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
        "description": {
            "hash": "7a90514f88c70002608a9868681dd1589ea598e78d00a8cd7783c3ea0f9ceb09",
            "storageAddress": "http://testserver/dataset/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/description/"
        },
        "key": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994",
        "name": "ISIC 2018",
        "nbData": 2,
        "openerStorageAddress": "http://testserver/dataset/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/opener/",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "size": 553113,
        "type": "Images"
    },
    {
        "challengeKey": "",
        "description": {
            "hash": "7a90514f88c70002608a9868681dd1589ea598e78d00a8cd7783c3ea0f9ceb08",
            "storageAddress": "http://testserver/dataset/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea995/description/"
        },
        "key": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea995",
        "name": "ISIC 2019",
        "nbData": 2,
        "openerStorageAddress": "http://testserver/dataset/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea995/opener/",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "size": 553113,
        "type": "Images"
    }
]

algo = [
    {
        "challengeKey": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
        "description": {
            "hash": "3b1281cbdd6ebfec650d0a9f932a64e45a27262848065d7cecf11fd7191b4b1f",
            "storageAddress": "http://testserver/algo/7742aea2001ceb40e9ce8a37fa27237d5b2d1f574e06d48677af945cfdf42ec0/description/"
        },
        "key": "7742aea2001ceb40e9ce8a37fa27237d5b2d1f574e06d48677af945cfdf42ec0",
        "name": "Logistic regression for balanced problem",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "storageAddress": "http://testserver/algo/7742aea2001ceb40e9ce8a37fa27237d5b2d1f574e06d48677af945cfdf42ec0/file/"
    },
    {
        "challengeKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "description": {
            "hash": "b9463411a01ea00869bdffce6e59a5c100a4e635c0a9386266cad3c77eb28e9e",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description/"
        },
        "key": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
        "name": "Neural Network",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
    },
    {
        "challengeKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/description/"
        },
        "key": "6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f",
        "name": "Logistic regression",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "storageAddress": "http://testserver/algo/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/file/"
    },
    {
        "challengeKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "description": {
            "hash": "4acea40c4b51996c88ef279c5c9aa41ab77b97d38c5ca167e978a98b2e402675",
            "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description/"
        },
        "key": "f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284",
        "name": "Random Forest",
        "owner": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "permissions": "all",
        "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/file/"
    }
]


traintuple = [
    {
        "algo": {
            "hash": "6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f",
            "name": "Logistic regression",
            "storageAddress": "http://testserver/algo/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/file/"
        },
        "challenge": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/challenge/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "creator": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1",
        "outModel": {
            "hash": "454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011",
            "storageAddress": "http://testserver/model/454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011/file/"
        },
        "key": "c164f4c714a78c7e2ba2016de231cdd41e3eac61289e08c1f711e74915a0868f",
        "log": "Train - CPU:75.04 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "permissions": "all",
        "startModel": None,
        "status": "done",
        "testData": {
            "keys": [
                "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"
            ],
            "openerHash": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
            "perf": 1,
            "worker": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1"
        },
        "trainData": {
            "keys": [
                "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
            ],
            "openerHash": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994",
            "perf": 1,
            "worker": "26b9f7e4bd2946e6c725778469d982c74bd65548bbf280bd59e793a7d14351f1"
        }
    }
]


# APITestCase
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'org': {'org_name': 'test-org'}, 'peer': 'test-peer'})
class ViewTests(APITestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        self.challenge_description, self.challenge_description_filename, \
            self.challenge_metrics, self.challenge_metrics_filename = get_sample_challenge()

        self.script, self.script_filename = get_sample_script()
        self.data_file, self.data_file_filename = get_sample_data()

        self.data_description, self.data_description_filename, \
            self.data_data_opener, self.data_opener_filename = get_sample_dataset()

        self.extra = {
            'HTTP_ACCEPT': 'application/json;version=0.0'
        }

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_traintuple_queryset(self):
        traintuple_view = TrainTupleViewSet()
        self.assertFalse(traintuple_view.get_queryset())

    def test_challenge_list_empty(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_challenge_list_filter_fail(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenERRORge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_challenge_list_filter_name(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASkin%2520Lesion%2520Classification%2520Challenge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_metrics(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Ametrics%253Amacro-average%2520recall'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_challenge_list_filter_dataset(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_algo(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            url = reverse('substrapp:challenge-list')
            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_list_filter_model(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(challenge, status.HTTP_200_OK),
                                        (model, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_challenge_retrieve(self):
        url = reverse('substrapp:challenge-list')
        with mock.patch('substrapp.views.challenge.getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(ChallengeViewSet, 'create_or_update_challenge') as mcreate_or_update_challenge:
            mgetObjectFromLedger.return_value = challenge[0]
            mcreate_or_update_challenge.return_value = Challenge.objects.create(description=self.challenge_description,
                                                                                metrics=self.challenge_metrics)

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, challenge[0])

    def test_challenge_retrieve_fail(self):
        url = reverse('substrapp:challenge-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.challenge.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_algo_list_empty(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_algo_list_filter_fail(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algERRORo'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_algo_list_filter_name(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_dataset(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_list_filter_challenge(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASkin%2520Lesion%2520Classification%2520Challenge'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 3)

    def test_algo_list_filter_model(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(algo, status.HTTP_200_OK),
                                        (model, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_algo_retrieve(self):
        url = reverse('substrapp:algo-list')
        with mock.patch('substrapp.views.algo.getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(AlgoViewSet, 'create_or_update_algo') as mcreate_or_update_algo:
            mgetObjectFromLedger.return_value = algo[3]
            mcreate_or_update_algo.return_value = Algo.objects.create(file=self.script)

            search_params = 'f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, algo[3])

    def test_algo_retrieve_fail(self):
        url = reverse('substrapp:algo-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.algo.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_list_empty(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_model_list_filter_fail(self):

        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK)]

            url = reverse('substrapp:model-list')
            search_params = '?search=modeERRORl'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()
            self.assertIn('Malformed search filters', r['message'])

    def test_model_list_filter_hash(self):

        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK)]

            url = reverse('substrapp:model-list')
            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_dataset(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253AISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_challenge(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASimplified%2520skin%2520lesion%2520classification'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_model_list_filter_algo(self):
        url = reverse('substrapp:model-list')
        with mock.patch('substrapp.views.model.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(model, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    # def test_model_retrieve(self):
    #     extra = {
    #         'HTTP_ACCEPT': 'application/json;version=0.0'
    #     }
    #
    #     with mock.patch('substrapp.views.model.getObjectFromLedger') as mgetObjectFromLedger:
    #         mgetObjectFromLedger.return_value = model[0]
    #
    #         url = reverse('substrapp:model-list')
    #         search_params = '454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011/'
    #         response = self.client.get(url + search_params, **self.extra)
    #         r = response.json()
    #
    #         self.assertEqual(r, model[0])

    def test_model_retrieve_fail(self):
        url = reverse('substrapp:model-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch('substrapp.views.model.getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dataset_list_empty(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(None, status.HTTP_200_OK),
                                        (['ISIC'], status.HTTP_200_OK)]

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [[]])

            response = self.client.get(url, **self.extra)
            r = response.json()
            self.assertEqual(r, [['ISIC']])

    def test_dataset_list_filter_fail(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK)]

            search_params = '?search=dataseERRORt'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertIn('Malformed search filters', r['message'])

    def test_dataset_list_filter_name(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK)]

            search_params = '?search=dataset%253Aname%253ASimplified%2520ISIC%25202018'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 1)

    def test_dataset_list_filter_algo(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (algo, status.HTTP_200_OK)]

            search_params = '?search=algo%253Aname%253ALogistic%2520regression%2520for%2520balanced%2520problem'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_list_filter_challenge(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (challenge, status.HTTP_200_OK)]

            search_params = '?search=challenge%253Aname%253ASimplified%2520skin%2520lesion%2520classification'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_list_filter_model(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch('substrapp.views.dataset.queryLedger') as mqueryLedger:
            mqueryLedger.side_effect = [(dataset, status.HTTP_200_OK),
                                        (model, status.HTTP_200_OK)]

            search_params = '?search=model%253Ahash%253A454511615090218bf9cef23b801a517d36045582c43ce7a908acb59b5174f011'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(len(r[0]), 2)

    def test_dataset_retrieve(self):
        url = reverse('substrapp:dataset-list')
        with mock.patch.object(DatasetViewSet, 'getObjectFromLedger') as mgetObjectFromLedger, \
                mock.patch.object(DatasetViewSet, 'create_or_update_dataset') as mcreate_or_update_dataset:
            mgetObjectFromLedger.return_value = dataset[1]
            mcreate_or_update_dataset.return_value = Dataset.objects.create(name='slide',
                                                                            description=self.data_description,
                                                                            data_opener=self.data_data_opener)

            search_params = 'ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/'
            response = self.client.get(url + search_params, **self.extra)
            r = response.json()

            self.assertEqual(r, dataset[1])

    def test_dataset_retrieve_fail(self):
        url = reverse('substrapp:dataset-list')

        # PK hash < 64 chars
        search_params = '42303efa663015e729159833a12ffb510ff/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # PK hash not hexa
        search_params = 'X' * 64 + '/'
        response = self.client.get(url + search_params, **self.extra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        with mock.patch.object(DatasetViewSet, 'getObjectFromLedger') as mgetObjectFromLedger:
            mgetObjectFromLedger.side_effect = JsonException('TEST')

            search_params = '6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/'
            response = self.client.get(url + search_params, **self.extra)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_data_path_view(self):
        self.assertEqual('tutu', path_leaf('/toto/tata/tutu'))
        self.assertEqual('toto', path_leaf('/toto/'))

    def test_utils_ComputeHashMixin(self):

        compute = ComputeHashMixin()
        myfile = 'toto'
        myfilehash = compute_hash(myfile)

        self.assertEqual(myfilehash, compute.compute_hash(myfile))
