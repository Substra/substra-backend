import shutil
import tempfile

from django.core.files import File
from django.test import TestCase
from django.test import override_settings

from substrapp.models import Algo
from substrapp.models import DataManager
from substrapp.models import DataSample
from substrapp.models import Metric
from substrapp.models import Model
from substrapp.utils import get_hash

from .common import get_sample_datamanager
from .common import get_sample_metric
from .common import get_sample_model
from .common import get_sample_script
from .common import get_sample_zip_data_sample

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ModelTests(TestCase):
    """Model tests"""

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create_metric(self):
        description, _, metrics, _ = get_sample_metric()
        metric = Metric.objects.create(description=description, address=metrics)

        self.assertEqual(metric.checksum, get_hash(description))

    def test_create_datamanager(self):
        description, _, data_opener, _ = get_sample_datamanager()
        datamanager = DataManager.objects.create(description=description, data_opener=data_opener, name="slides_opener")
        self.assertEqual(datamanager.checksum, get_hash(data_opener))

    def test_create_data(self):
        data_file, _ = get_sample_zip_data_sample()
        data_sample = DataSample.objects.create(file=File(data_file), checksum="checksum")
        self.assertEqual(data_sample.checksum, "checksum")

    def test_create_algo(self):
        script, _ = get_sample_script()
        algo = Algo.objects.create(file=script)
        self.assertEqual(algo.checksum, get_hash(script))

    def test_create_model(self):
        modelfile, _ = get_sample_model()
        model = Model.objects.create(file=modelfile)
        self.assertEqual(model.checksum, get_hash(modelfile))
