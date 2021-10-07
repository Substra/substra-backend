import shutil
import tempfile

from django.core.files import File
from django.test import TestCase, override_settings

from substrapp.models import Objective, DataManager, DataSample, Algo, Model
from substrapp.utils import get_hash

from .common import get_sample_objective, get_sample_datamanager, \
    get_sample_script, get_sample_model, get_sample_zip_data_sample

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create_objective(self):
        description, _, metrics, _ = get_sample_objective()
        objective = Objective.objects.create(description=description,
                                             metrics=metrics)

        self.assertEqual(objective.checksum, get_hash(description))
        self.assertFalse(objective.validated)
        self.assertIn(f'key {objective.key}', str(objective))
        self.assertIn(f'validated {objective.validated}', str(objective))

    def test_create_datamanager(self):
        description, _, data_opener, _ = get_sample_datamanager()
        datamanager = DataManager.objects.create(description=description, data_opener=data_opener, name="slides_opener")
        self.assertEqual(datamanager.checksum, get_hash(data_opener))
        self.assertFalse(datamanager.validated)
        self.assertIn(f'key {datamanager.key}', str(datamanager))
        self.assertIn(f'name {datamanager.name}', str(datamanager))

    def test_create_data(self):
        data_file, _ = get_sample_zip_data_sample()
        data_sample = DataSample.objects.create(file=File(data_file), checksum="checksum")
        self.assertFalse(data_sample.validated)
        self.assertIn(f'key {data_sample.key}', str(data_sample))
        self.assertIn(f'validated {data_sample.validated}', str(data_sample))

    def test_create_algo(self):
        script, _ = get_sample_script()
        algo = Algo.objects.create(file=script)
        self.assertEqual(algo.checksum, get_hash(script))
        self.assertFalse(algo.validated)
        self.assertIn(f'key {algo.key}', str(algo))
        self.assertIn(f'validated {algo.validated}', str(algo))

    def test_create_model(self):
        modelfile, _ = get_sample_model()
        model = Model.objects.create(file=modelfile)
        self.assertEqual(model.checksum, get_hash(modelfile))
        self.assertFalse(model.validated)
        self.assertIn(f'key {model.key}', str(model))
        self.assertIn(f'validated {model.validated}', str(model))
