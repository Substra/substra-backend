from django.test import TestCase, override_settings
from django.core.management import call_command
from rest_framework import status

import json
import os
import sys
from io import StringIO
import shutil
from mock import patch

from substrapp.models import Challenge
from substrapp.serializers import LedgerChallengeSerializer, \
    LedgerDatasetSerializer, LedgerDataSerializer

MEDIA_ROOT = "/tmp/unittests_misc/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(SITE_HOST='localhost')
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class CreateObjectiveTestCase(TestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_createobjective(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip'))
        data_path2 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip'))

        dataset_opener_path = os.path.normpath(os.path.join(dir_path,
                                                            '../../fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/opener.py'))
        dataset_description_path = os.path.normpath(os.path.join(dir_path,
                                                                 '../../fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/description.md'))

        objective_metrics_path = os.path.normpath(os.path.join(dir_path,
                                                            '../../fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py'))
        objective_description_path = os.path.normpath(os.path.join(dir_path,
                                                                 '../../fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md'))

        data = {
            'objective': {
                'name': 'foo',
                'metrics_name': 'accuracy',
                'metrics': objective_metrics_path,
                'description': objective_description_path
            },
            'dataset': {
                'name': 'foo',
                'type': 'bar',
                'data_opener': dataset_opener_path,
                'description': dataset_description_path
            },
            'data': {
                'paths': [data_path1, data_path2],
                'test_only': False
            }
        }

        objective_pk = 'd5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f'
        dataset_pk = '59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd'
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(LedgerChallengeSerializer, 'create') as mobjectivecreate, \
                patch.object(LedgerDatasetSerializer, 'create') as mdatasetcreate, \
                patch('substrapp.management.commands.createobjective.updateLedgerDataset') as mdatasetupdate, \
                patch.object(LedgerDataSerializer, 'create') as mdatacreate, \
                patch('substrapp.views.data.DataViewSet.check_datasets') as mcheck_datasets:

            mobjectivecreate.return_value = ({
                                               'pkhash': objective_pk,
                                               'validated': True
                                           },
                                           status.HTTP_201_CREATED)
            mdatasetcreate.return_value = ({
                                               'pkhash': dataset_pk,
                                               'validated': True
                                           },
                                           status.HTTP_201_CREATED)
            mdatacreate.return_value = ({
                                            'pkhash': [pkhash1, pkhash2],
                                            'validated': True
                                        },
                                        status.HTTP_201_CREATED)

            mdatasetupdate.return_value = ({
                                            'pkhash': dataset_pk
                                        },
                                        status.HTTP_201_CREATED)

            mcheck_datasets.return_value = True

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

                dataset_out = {
                        "pkhash": dataset_pk,
                        "validated": True
                    }

                data_out = [
                    {
                        "pkhash": pkhash1,
                        "path": os.path.join(MEDIA_ROOT, 'data', pkhash1),
                        "validated": True
                    },
                    {
                        "pkhash": pkhash2,
                        "path": os.path.join(MEDIA_ROOT, 'data', pkhash2),
                        "validated": True
                    }
                ]

                dataset_updated_out = {
                    "pkhash": dataset_pk
                }

                dataset = json.dumps(dataset_out, indent=4)
                data = json.dumps(data_out, indent=4)
                objective = json.dumps(objective_out, indent=4)
                dataset_updated = json.dumps(dataset_updated_out, indent=4)
                dataset_wanted_output = f'Successfully added dataset with status code {status.HTTP_201_CREATED} and result: {dataset}'
                data_wanted_output = f'Successfully bulk added data with status code {status.HTTP_201_CREATED} and result: {data}'
                objective_wanted_output = f'Successfully added objective with status code {status.HTTP_201_CREATED} and result: {objective}'
                dataset_updated_wanted_output = f'Successfully updated dataset with status code {status.HTTP_201_CREATED} and result: {dataset_updated}'
                self.assertEqual(output, f'{dataset_wanted_output}\nWill add data to this dataset now\n{data_wanted_output}\nWill add objective to this dataset now\n{objective_wanted_output}\nWill update dataset with this objective now\n{dataset_updated_wanted_output}')
            finally:
                sys.stdout = saved_stdout

    def test_createdataset_ko_409(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip'))
        data_path2 = os.path.normpath(os.path.join(dir_path,
                                                   '../../fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip'))

        dataset_opener_path = os.path.normpath(os.path.join(dir_path,
                                                            '../../fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/opener.py'))
        dataset_description_path = os.path.normpath(os.path.join(dir_path,
                                                                 '../../fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/description.md'))

        data = {
            'dataset': {
                'name': 'foo',
                'type': 'bar',
                'data_opener': dataset_opener_path,
                'description': dataset_description_path
            },
            'data': {
                'paths': [data_path1, data_path2],
                'test_only': False
            }
        }

        dataset_pk = '678912ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        # create dataset
        # d = Dataset(pkhash=dataset_pk, name='foo', data_opener=dataset_opener_path, description=dataset_description_path)
        # d.save()

        with patch.object(LedgerDatasetSerializer, 'create') as mdatasetcreate, \
                patch.object(LedgerDataSerializer, 'create') as mdatacreate, \
                patch(
                    'substrapp.views.data.DataViewSet.check_datasets') as mcheck_datasets:

            mdatasetcreate.return_value = ({
                                               'message': 'dataset already exists',
                                           },
                                           status.HTTP_409_CONFLICT)
            mdatacreate.return_value = ({
                                            'pkhash': [pkhash1, pkhash2],
                                            'validated': True
                                        },
                                        status.HTTP_201_CREATED)
            mcheck_datasets.return_value = True

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                err = StringIO()
                sys.stdout = out
                sys.stderr = err
                call_command('createdataset', json.dumps(data))

                output = out.getvalue().strip()
                err_output = err.getvalue().strip()

                dataset_out = {
                        "message": 'dataset already exists',
                    }

                data_out = [
                    {
                        "pkhash": pkhash1,
                        "path": os.path.join(MEDIA_ROOT, 'data', pkhash1),
                        "validated": True
                    },
                    {
                        "pkhash": pkhash2,
                        "path": os.path.join(MEDIA_ROOT, 'data', pkhash2),
                        "validated": True
                    }
                ]

                dataset = json.dumps(dataset_out, indent=2)
                data = json.dumps(data_out, indent=4)
                data_wanted_output = f'Successfully bulk added data with status code {status.HTTP_201_CREATED} and result: {data}'
                self.assertEqual(output, f'Will add data to this dataset now\n{data_wanted_output}')
                self.assertEqual(err_output, dataset)
            finally:
                sys.stdout = saved_stdout
