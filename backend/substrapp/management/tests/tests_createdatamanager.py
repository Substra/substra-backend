from django.test import TestCase, override_settings
from django.core.management import call_command
from rest_framework import status

import json
import os
import sys
from io import StringIO
import shutil
from mock import patch

from substrapp.serializers import LedgerDataSampleSerializer, LedgerDataManagerSerializer

from substrapp.utils import get_hash

MEDIA_ROOT = "/tmp/unittests_misc/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class CreateDataManagerTestCase(TestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_createdatamanager(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))
        data_path2 = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip'))

        datamanager_opener_path = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))
        datamanager_description_path = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/description.md'))

        data = {
            'data_manager': {
                'name': 'foo',
                'type': 'bar',
                'data_opener': datamanager_opener_path,
                'description': datamanager_description_path
            },
            'data_samples': {
                'paths': [data_path1, data_path2],
                'test_only': False
            }
        }

        datamanager_pk = get_hash(datamanager_opener_path)
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(LedgerDataManagerSerializer, 'create') as mdatamanagercreate, \
                patch.object(LedgerDataSampleSerializer, 'create') as mdatacreate, \
                patch(
                    'substrapp.views.datasample.DataSampleViewSet.check_datamanagers') as mcheck_datamanagers:

            mdatamanagercreate.return_value = ({
                'pkhash': datamanager_pk,
                'validated': True
            }, status.HTTP_201_CREATED)
            mdatacreate.return_value = ({
                'pkhash': [pkhash1, pkhash2],
                'validated': True
            }, status.HTTP_201_CREATED)
            mcheck_datamanagers.return_value = True

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out
                call_command('createdataset', json.dumps(data))

                output = out.getvalue().strip()

                datamanager_out = {
                    "pkhash": datamanager_pk,
                    "validated": True
                }

                data_out = [
                    {
                        "pkhash": pkhash1,
                        "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash1),
                        "validated": True
                    },
                    {
                        "pkhash": pkhash2,
                        "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash2),
                        "validated": True
                    }
                ]

                datamanager = json.dumps(datamanager_out, indent=4)
                data = json.dumps(data_out, indent=4)
                datamanager_wanted_output = f'Successfully added datamanager with status code ' \
                                            f'{status.HTTP_201_CREATED} and result: {datamanager}'
                data_wanted_output = f'Successfully bulk added data samples with status code ' \
                                     f'{status.HTTP_201_CREATED} and result: {data}'
                self.assertEqual(output, f'{datamanager_wanted_output}\nWill add data to this datamanager now'
                                         f'\n{data_wanted_output}')
            finally:
                sys.stdout = saved_stdout

    def test_createdatamanager_ko_409(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))
        data_path2 = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip'))

        datamanager_opener_path = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))
        datamanager_description_path = os.path.normpath(os.path.join(
            dir_path, '../../../fixtures/chunantes/datamanagers/datamanager0/description.md'))

        data = {
            'data_manager': {
                'name': 'foo',
                'type': 'bar',
                'data_opener': datamanager_opener_path,
                'description': datamanager_description_path
            },
            'data_samples': {
                'paths': [data_path1, data_path2],
                'test_only': False
            }
        }

        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(LedgerDataManagerSerializer, 'create') as mdatamanagercreate, \
                patch.object(LedgerDataSampleSerializer, 'create') as mdatacreate, \
                patch(
                    'substrapp.views.datasample.DataSampleViewSet.check_datamanagers') as mcheck_datamanagers:

            mdatamanagercreate.return_value = ({
                'message': 'datamanager already exists',
            }, status.HTTP_409_CONFLICT)
            mdatacreate.return_value = ({
                'pkhash': [pkhash1, pkhash2],
                'validated': True
            }, status.HTTP_201_CREATED)
            mcheck_datamanagers.return_value = True

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                err = StringIO()
                sys.stdout = out
                sys.stderr = err
                call_command('createdataset', json.dumps(data))

                output = out.getvalue().strip()
                err_output = err.getvalue().strip()

                datamanager_out = {
                    "message": 'datamanager already exists',
                }

                data_out = [
                    {
                        "pkhash": pkhash1,
                        "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash1),
                        "validated": True
                    },
                    {
                        "pkhash": pkhash2,
                        "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash2),
                        "validated": True
                    }
                ]

                datamanager = json.dumps(datamanager_out, indent=2)
                data = json.dumps(data_out, indent=4)
                data_wanted_output = f'Successfully bulk added data samples with status code ' \
                                     f'{status.HTTP_201_CREATED} and result: {data}'
                self.assertEqual(output, f'Will add data to this datamanager now\n{data_wanted_output}')
                self.assertEqual(err_output, datamanager)
            finally:
                sys.stdout = saved_stdout
