from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from api.models.utils import URLValidatorWithOptionalTLD


class ModelUtilsTests(TestCase):
    """Test serializers utils"""

    def test_url_validator(self):
        """test that DRF URL validator is not valid while the custom validator is"""
        custom_url_valid = "http://backend.org-1"

        custom_url_validator = URLValidatorWithOptionalTLD()
        drf_url_validator = URLValidator()

        custom_url_validator(custom_url_valid)
        with self.assertRaises(ValidationError):
            drf_url_validator(custom_url_valid)
