import os
import mock
import tempfile
import uuid
from django.test import override_settings
from rest_framework.test import APITestCase
from substrapp.tasks.tasks import build_subtuple_folders, do_task, TRAINTUPLE_TYPE
from substrapp.utils import get_cp_local_folder
from parameterized import parameterized

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class LocalFolderTests(APITestCase):

    # This test ensures that changes to the subtuple local folder are
    # reflected to the compute plan local folder iff the tuple execution succeeds.
    @parameterized.expand([
        ("without_exception", True),
        ("with_exception", False)
    ])
    def test_local_folder(self, _, compute_job_raises):
        channel_name = 'dummy_channel'
        compute_plan_tag = 'cp1'
        compute_plan_key = str(uuid.uuid4())

        file = 'model.txt'
        initial_value = 'initial value'
        updated_value = 'updated value'

        subtuple = {
            'key': str(uuid.uuid4()),
            'compute_plan_key': compute_plan_key,
            'rank': 1,
            'algo': {
                'key': 'some key'
            }
        }

        # Write an initial value into the compute plan local folder
        cp_local_folder = get_cp_local_folder(compute_plan_key)
        os.makedirs(cp_local_folder, exist_ok=True)
        with open(os.path.join(cp_local_folder, file), 'w') as x:
            x.write(initial_value)

        # Call `do_task`, which will:
        # 1. write a new value to the subtuple local folder
        # 2. and then:
        #    - complete successfully (compute_job_raises == False)
        #    - or raise an exception (compute_job_raises == True)
        with mock.patch('substrapp.ledger.api.query_ledger') as mquery_ledger,\
             mock.patch('substrapp.tasks.tasks.generate_command'),\
             mock.patch('substrapp.tasks.tasks.save_models'),\
             mock.patch('substrapp.tasks.tasks.compute_job') as mcompute_job:
            mquery_ledger.return_value = {'tag': compute_plan_tag}

            def compute_job(*args, **kwargs):
                for vol in kwargs['volumes']:
                    if vol.endswith('/local'):
                        with open(os.path.join(vol, file), 'w') as x:
                            x.write(updated_value)
                if compute_job_raises:
                    raise Exception('Boom!')

            mcompute_job.side_effect = compute_job
            try:
                build_subtuple_folders(subtuple)
                do_task(channel_name, subtuple, TRAINTUPLE_TYPE)
            except Exception:
                pass

        # Check the compute plan local folder value is correct:
        # - If do_task did raise an exception then the local value should be unchanged
        # - If do_task did not raise an exception then the local value should be updated
        with open(os.path.join(cp_local_folder, file), 'r') as x:
            content = x.read()
        self.assertEqual(content, initial_value if compute_job_raises else updated_value)
