from django.test import TestCase
from substrapp.utils import raise_if_path_traversal

import os


DIRECTORY = '/tmp/testmisc/'


class MiscTests(TestCase):
    """Misc tests"""

    def test_uncompress_path_path_traversal_model(self):
        with self.assertRaises(Exception):
            model_dst_path = os.path.join(DIRECTORY, 'model/../../hackermodel')
            raise_if_path_traversal([model_dst_path], os.path.join(DIRECTORY, 'model/'))
