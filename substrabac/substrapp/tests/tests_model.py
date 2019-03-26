import os
import shutil
import tempfile

from checksumdir import dirhash
from coreapi.utils import File
from django.test import TestCase, override_settings
from mock import MagicMock

from substrapp.models import Challenge, Dataset, Data, Algo, Model
from substrapp.utils import get_hash, get_dir_hash

from .common import get_sample_challenge, get_sample_dataset, get_sample_data, \
    get_sample_script, get_sample_model, get_sample_zip_data

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def tearDown(self):
        try:
            shutil.rmtree(MEDIA_ROOT)
        except FileNotFoundError:
            pass

    def test_create_challenge(self):
        description, _, metrics, _ = get_sample_challenge()
        challenge = Challenge.objects.create(description=description,
                                             metrics=metrics)

        self.assertEqual(challenge.pkhash, get_hash(description))
        self.assertFalse(challenge.validated)
        self.assertIn(f'pkhash {challenge.pkhash}', str(challenge))
        self.assertIn(f'validated {challenge.validated}', str(challenge))

    def test_create_dataset(self):
        description, _, data_opener, _ = get_sample_dataset()
        dataset = Dataset.objects.create(description=description, data_opener=data_opener, name="slides_opener")
        self.assertEqual(dataset.pkhash, get_hash(data_opener))
        self.assertFalse(dataset.validated)
        self.assertIn(f'pkhash {dataset.pkhash}', str(dataset))
        self.assertIn(f'name {dataset.name}', str(dataset))

    def test_create_data(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dir_path, '../../fixtures/chunantes/data/train/0024308')
        data = Data.objects.create(path=path)
        self.assertEqual(data.pkhash, dirhash(path, 'sha256'))
        self.assertFalse(data.validated)
        self.assertIn(f'pkhash {data.pkhash}', str(data))
        self.assertIn(f'validated {data.validated}', str(data))

    def test_create_algo(self):
        script, _ = get_sample_script()
        algo = Algo.objects.create(file=script)
        self.assertEqual(algo.pkhash, get_hash(script))
        self.assertFalse(algo.validated)
        self.assertIn(f'pkhash {algo.pkhash}', str(algo))
        self.assertIn(f'validated {algo.validated}', str(algo))

    def test_create_model(self):
        modelfile, _ = get_sample_model()
        model = Model.objects.create(file=modelfile)
        self.assertEqual(model.pkhash, get_hash(modelfile))
        self.assertFalse(model.validated)
        self.assertIn(f'pkhash {model.pkhash}', str(model))
        self.assertIn(f'validated {model.validated}', str(model))
