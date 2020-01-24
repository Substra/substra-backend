import zipfile

from django.core.files import File
from django.test import TestCase, override_settings
from django.core.management import call_command, CommandError
from rest_framework import status
from unittest.mock import MagicMock, mock_open

import json
import os
import sys
from io import StringIO
import shutil
from mock import patch

from substrapp.models import DataManager
from substrapp.serializers import LedgerDataSampleSerializer, DataSampleSerializer
from substrapp.tests.common import get_sample_zip_data_sample
from substrapp.views import DataSampleViewSet
from substrapp.views.datasample import LedgerException

from substrapp.utils import get_hash

MEDIA_ROOT = "/tmp/unittests_misc/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@override_settings(LEDGER={'name': 'test-org', 'peer': 'test-peer'})
class BulkCreateDataSampleTestCase(TestCase):

    def setUp(self):
        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        mock_description = MagicMock(spec=File)
        mock_description.name = 'description.md'
        mock_description.read = MagicMock(return_value=b'desc')
        mock_description.open = MagicMock(return_value=mock_description)

        mock_data_opener = MagicMock(spec=File)
        mock_data_opener.name = 'opener.py'
        mock_data_opener.read = MagicMock(return_value=b'import os')
        mock_data_opener.open = MagicMock(return_value=mock_data_opener)

        self.datamanager = DataManager.objects.create(name='slide opener',
                                                      description=mock_description,
                                                      data_opener=mock_data_opener)

        self.data_sample_file, self.data_sample_file_filename = get_sample_zip_data_sample()

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_bulkcreatedatasample(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(
            os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))
        data_path2 = os.path.normpath(
            os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1, data_path2],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        # dir hash
        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1, pkhash2],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out
                call_command('bulkcreatedatasample', json.dumps(data))

                output = out.getvalue().strip()

                out_data = [
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
                data = json.dumps(out_data, indent=4)
                wanted_output = f'Successfully added data samples via bulk with status code ' \
                                f'{status.HTTP_201_CREATED} and data: {data}'
                self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_path(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(
            os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/train/0024308'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        pkhash1 = get_hash(data_path1)

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out

                # mock hard links to simulate we are on the same partition
                with patch(
                        'substrapp.signals.datasample.pre_save.create_hard_links') as mcreate_hard_links:
                    mcreate_hard_links.return_value = True

                    call_command('bulkcreatedatasample', json.dumps(data))

                    output = out.getvalue().strip()

                    out_data = [
                        {
                            "pkhash": pkhash1,
                            "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash1),
                            "validated": True
                        },
                    ]
                    data = json.dumps(out_data, indent=4)
                    wanted_output = f'Successfully added data samples via bulk with status code ' \
                                    f'{status.HTTP_201_CREATED} and data: {data}'
                    self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_original_path(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/train/0024308'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        pkhash1 = get_hash(data_path1)

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out

                # mock hard links to simulate we are on another partition
                with patch('substrapp.signals.datasample.pre_save.create_hard_links') as mcreate_hard_links:
                    mcreate_hard_links.side_effect = Exception('Fail')

                    call_command('bulkcreatedatasample', json.dumps(data))

                    output = out.getvalue().strip()

                    out_data = [
                        {
                            "pkhash": pkhash1,
                            "path": data_path1,
                            "validated": True
                        },
                    ]
                    data = json.dumps(out_data, indent=4)
                    wanted_output = f'Successfully added data samples via bulk with status code ' \
                                    f'{status.HTTP_201_CREATED} and data: {data}'
                    self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_path_and_files(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/train/0024308'))
        data_path2 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/datasample0/0024899.zip'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1, data_path2],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        # dir hash
        pkhash1 = 'e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c'
        pkhash2 = '30f6c797e277451b0a08da7119ed86fb2986fa7fab2258bf3edbd9f1752ed553'

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1, pkhash2],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                out = StringIO()
                sys.stdout = out

                # mock hard links as we are on /tmp which is on another patition
                with patch(
                        'substrapp.signals.datasample.pre_save.create_hard_links') as mcreate_hard_links:
                    mcreate_hard_links.return_value = True

                    call_command('bulkcreatedatasample', json.dumps(data))

                    output = out.getvalue().strip()

                    out_data = [
                        {
                            "pkhash": pkhash1,
                            "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash1),
                            "validated": True
                        },
                        {
                            "pkhash": pkhash2,
                            "path": os.path.join(MEDIA_ROOT, 'datasamples', pkhash2),
                            "validated": True
                        },
                    ]
                    data = json.dumps(out_data, indent=4)
                    wanted_output = f'Successfully added data samples via bulk with status code ' \
                                    f'{status.HTTP_201_CREATED} and data: {data}'
                    self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_same_on_file(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1, data_path1],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1, pkhash1],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                err = StringIO()
                sys.stderr = err
                call_command('bulkcreatedatasample', json.dumps(data))

                output = err.getvalue().strip()

                wanted_output = f'Your data sample archives/paths contain same files leading to same pkhash, ' \
                                f'please review the content of your achives/paths. ' \
                                f'{data_path1} and 0024700.zip are the same'
                self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_same_on_path(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/train/0024308'))

        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'paths': [data_path1, data_path1],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        pkhash1 = '24fb12ff87485f6b0bc5349e5bf7f36ccca4eb1353395417fdae7d8d787f178c'

        with patch.object(DataManager.objects, 'filter') as mdatamanager, \
                patch.object(LedgerDataSampleSerializer, 'create') as mcreate:

            mcreate.return_value = ({'pkhash': [pkhash1, pkhash1],
                                     'validated': True},
                                    status.HTTP_201_CREATED)

            mock_filter = MagicMock()
            mock_filter.count.return_value = 1
            mdatamanager.return_value = mock_filter

            saved_stdout = sys.stdout

            try:
                err = StringIO()
                sys.stderr = err
                call_command('bulkcreatedatasample', json.dumps(data))

                output = err.getvalue().strip()

                wanted_output = f'Your data sample archives/paths contain same files leading to same pkhash, ' \
                                f'please review the content of your achives/paths. ' \
                                f'{data_path1} and {data_path1} are the same'
                self.assertEqual(wanted_output, output)
            finally:
                sys.stdout = saved_stdout

    def test_bulkcreatedatasample_not_a_list(self):

        data = {'paths': 'tutu',
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        err = StringIO()
        sys.stderr = err

        call_command('bulkcreatedatasample', json.dumps(data))

        output = err.getvalue().strip()

        self.assertEqual(output,
                         'Please specify a list of paths (can be archives or directories)')

    def test_bulkcreatedatasample_invalid_json_dict(self):

        data = 'tutu'

        err = StringIO()
        sys.stderr = err

        with self.assertRaises(CommandError):
            call_command('bulkcreatedatasample', json.dumps(data))

    def test_bulkcreatedatasample_invalid_json_args(self):

        err = StringIO()
        sys.stderr = err

        with self.assertRaises(CommandError):
            call_command('bulkcreatedatasample', '(')

    def test_bulkcreatedatasample_valid_path(self):

        err = StringIO()
        sys.stderr = err

        with patch('substrapp.management.commands.bulkcreatedatasample.open',
                   mock_open(read_data='{"toto": 1}')) as mopen:
            call_command('bulkcreatedatasample', './foo')
            mopen.assert_called_once_with('./foo', 'r')

    def test_bulkcreatedatasample_invalid_datamanager(self):

        data = {'paths': ['./foo'],
                'data_manager_keys': ['bar'],
                'test_only': False}

        err = StringIO()
        sys.stderr = err
        call_command('bulkcreatedatasample', json.dumps(data))

        output = err.getvalue().strip()

        wanted_output = "One or more datamanager keys provided do not exist in local database. "\
                        "Please create them before. DataManager keys: ['bar']"

        self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_not_array_datamanager(self):

        data = {'paths': ['./foo'],
                'data_manager_keys': 'bar',
                'test_only': False}

        err = StringIO()
        sys.stderr = err
        call_command('bulkcreatedatasample', json.dumps(data))

        output = err.getvalue().strip()

        wanted_output = "The data_manager_keys you provided is not an array"

        self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_datamanager_do_not_exist(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        data_manager_keys = [
            get_hash(os.path.join(dir_path, '../../../fixtures/owkin/datamanagers/datamanager0/opener.py'))]

        data = {'files': ['./foo'],
                'data_manager_keys': data_manager_keys,
                'test_only': False}

        err = StringIO()
        sys.stderr = err
        call_command('bulkcreatedatasample', json.dumps(data))

        output = err.getvalue().strip()

        wanted_output = f"One or more datamanager keys provided do not exist in local database. " \
                        f"Please create them before. DataManager keys: {data_manager_keys}"

        self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_invalid_file(self):
        data = {'paths': ['./foo'],
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        err = StringIO()
        sys.stderr = err
        call_command('bulkcreatedatasample', json.dumps(data))

        output = err.getvalue().strip()

        wanted_output = "File or Path: ./foo does not exist"

        self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_invalid_serializer(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        data_path1 = os.path.normpath(
            os.path.join(dir_path, '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))

        data = {'paths': [data_path1],
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        err = StringIO()
        sys.stderr = err

        with patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
                patch.object(os.path, 'exists') as mexists, \
                patch('substrapp.management.commands.bulkcreatedatasample.open',
                      mock_open(read_data=self.data_sample_file.read())), \
                patch('substrapp.management.commands.bulkcreatedatasample.DataSampleSerializer',
                      spec=True) as mDataSampleSerializer:  # noqa: N806
            mis_zipfile.return_value = True
            mexists.return_value = True

            mocked_serializer = MagicMock(DataSampleSerializer)
            mocked_serializer.is_valid.side_effect = Exception('Failed')
            mDataSampleSerializer.return_value = mocked_serializer

            call_command('bulkcreatedatasample', json.dumps(data))

            output = err.getvalue().strip()

            wanted_output = "Failed"

            self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_408(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))

        data = {'paths': [data_path1],
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        out = StringIO()
        sys.stdout = out

        with patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
                patch.object(os.path, 'exists') as mexists, \
                patch('substrapp.management.commands.bulkcreatedatasample.open',
                      mock_open(read_data=self.data_sample_file.read())), \
                patch.object(DataSampleViewSet, 'commit') as mcommit, \
                patch('substrapp.management.commands.bulkcreatedatasample.DataSampleSerializer',
                      spec=True) as mDataSampleSerializer:  # noqa: N806
            mis_zipfile.return_value = True
            mexists.return_value = True

            mocked_serializer = MagicMock(DataSampleSerializer)
            mocked_serializer.is_valid.return_value = True
            mDataSampleSerializer.return_value = mocked_serializer

            err_data = {'toto': 1}
            mcommit.side_effect = LedgerException(err_data,
                                                  status.HTTP_408_REQUEST_TIMEOUT)

            call_command('bulkcreatedatasample', json.dumps(data))

            output = out.getvalue().strip()

            wanted_output = json.dumps(err_data, indent=2)

            self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_ledger_400(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))

        data = {'paths': [data_path1],
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        err = StringIO()
        sys.stderr = err

        with patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
                patch.object(os.path, 'exists') as mexists, \
                patch('substrapp.management.commands.bulkcreatedatasample.open',
                      mock_open(read_data=self.data_sample_file.read())), \
                patch.object(DataSampleViewSet, 'commit') as mcommit, \
                patch('substrapp.management.commands.bulkcreatedatasample.DataSampleSerializer',
                      spec=True) as mDataSampleSerializer:  # noqa: N806
            mis_zipfile.return_value = True
            mexists.return_value = True

            mocked_serializer = MagicMock(DataSampleSerializer)
            mocked_serializer.is_valid.return_value = True
            mDataSampleSerializer.return_value = mocked_serializer

            err_data = {'toto': 1}
            mcommit.side_effect = LedgerException(err_data,
                                                  status.HTTP_400_BAD_REQUEST)

            call_command('bulkcreatedatasample', json.dumps(data))

            output = err.getvalue().strip()

            wanted_output = json.dumps(err_data, indent=2)

            self.assertEqual(wanted_output, output)

    def test_bulkcreatedatasample_400(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        data_path1 = os.path.normpath(os.path.join(dir_path,
                                                   '../../../fixtures/chunantes/datasamples/datasample1/0024700.zip'))

        data = {'paths': [data_path1],
                'data_manager_keys': [self.datamanager.pk],
                'test_only': False}

        err = StringIO()
        sys.stderr = err

        with patch.object(zipfile, 'is_zipfile') as mis_zipfile, \
                patch.object(os.path, 'exists') as mexists, \
                patch('substrapp.management.commands.bulkcreatedatasample.open',
                      mock_open(read_data=self.data_sample_file.read())), \
                patch.object(DataSampleViewSet, 'commit') as mcommit, \
                patch('substrapp.management.commands.bulkcreatedatasample.DataSampleSerializer',
                      spec=True) as mDataSampleSerializer:  # noqa: N806
            mis_zipfile.return_value = True
            mexists.return_value = True

            mocked_serializer = MagicMock(DataSampleSerializer)
            mocked_serializer.is_valid.return_value = True
            mDataSampleSerializer.return_value = mocked_serializer

            mcommit.side_effect = Exception('Failed',
                                            status.HTTP_400_BAD_REQUEST)

            call_command('bulkcreatedatasample', json.dumps(data))

            output = err.getvalue().strip()

            wanted_output = "('Failed', 400)"

            self.assertEqual(wanted_output, output)
