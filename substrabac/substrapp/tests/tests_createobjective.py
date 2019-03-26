from django.test import TestCase, override_settings
from django.core.management import call_command
from rest_framework import status

import json
import os
import sys
from io import StringIO
import shutil
from mock import patch

from substrapp.serializers import LedgerObjectiveSerializer, \
    LedgerDataManagerSerializer, LedgerDataSampleSerializer

MEDIA_ROOT = "/tmp/unittests_misc/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class CreateObjectiveTestCase(TestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)
        self.maxDiff = None

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_createobjective(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))
        data_path2 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/datasamples/datasample0/0024899.zip'))

        datamanager_opener_path = os.path.normpath(os.path.join(dir_path,
                                                                '../../fixtures/chunantes/datamanagers/datamanager0/opener.py'))
        datamanager_description_path = os.path.normpath(os.path.join(dir_path,
                                                                     '../../fixtures/chunantes/datamanagers/datamanager0/description.md'))
        objective_metrics_path = os.path.normpath(os.path.join(dir_path,
                                                            '../../fixtures/chunantes/objectives/objective0/metrics.py'))
        objective_description_path = os.path.normpath(os.path.join(dir_path,
                                                                 '../../fixtures/chunantes/objectives/objective0/description.md'))

        data = {
            'objective': {
                'name': 'foo',
                'metrics_name': 'accuracy',
                'metrics': objective_metrics_path,
                'description': objective_description_path
            },
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

        objective_pk = 'd5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f'
        datamanager_pk = '59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd'
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(LedgerObjectiveSerializer, 'create') as mobjectivecreate, \
                patch.object(LedgerDataManagerSerializer, 'create') as mdatamanagercreate, \
                patch('substrapp.management.commands.createobjective.updateLedgerDataManager') as mdatamanagerupdate, \
                patch.object(LedgerDataSampleSerializer, 'create') as mdatacreate, \
                patch('substrapp.views.datasample.DataSampleViewSet.check_datamanagers') as mcheck_datamanagers:

            mobjectivecreate.return_value = ({
                                               'pkhash': objective_pk,
                                               'validated': True
                                           },
                                           status.HTTP_201_CREATED)
            mdatamanagercreate.return_value = ({
                                               'pkhash': datamanager_pk,
                                               'validated': True
                                           },
                                           status.HTTP_201_CREATED)
            mdatacreate.return_value = ({
                                            'pkhash': [pkhash1, pkhash2],
                                            'validated': True
                                        },
                                        status.HTTP_201_CREATED)

            mdatamanagerupdate.return_value = ({
                                            'pkhash': datamanager_pk
                                        },
                                        status.HTTP_201_CREATED)

            mcheck_datamanagers.return_value = True

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out
                call_command('createobjective', json.dumps(data))

                output = out.getvalue().strip()

                objective_out = {
                    "pkhash": objective_pk,
                    "validated": True
                }

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

                datamanager_updated_out = {
                    "pkhash": datamanager_pk
                }

                datamanager = json.dumps(datamanager_out, indent=4)
                data = json.dumps(data_out, indent=4)
                objective = json.dumps(objective_out, indent=4)
                datamanager_updated = json.dumps(datamanager_updated_out, indent=4)
                datamanager_wanted_output = f'Successfully added datamanager with status code {status.HTTP_201_CREATED} and result: {datamanager}'
                data_wanted_output = f'Successfully bulk added data samples with status code {status.HTTP_201_CREATED} and result: {data}'
                objective_wanted_output = f'Successfully added objective with status code {status.HTTP_201_CREATED} and result: {objective}'
                datamanager_updated_wanted_output = f'Successfully updated datamanager with status code {status.HTTP_201_CREATED} and result: {datamanager_updated}'
                self.assertEqual(output, f'{datamanager_wanted_output}\nWill add data samples to this datamanager now\n{data_wanted_output}\nWill add objective to this datamanager now\n{objective_wanted_output}\nWill update datamanager with this objective now\n{datamanager_updated_wanted_output}')
            finally:
                sys.stdout = saved_stdout
