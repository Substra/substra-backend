from django.test import TestCase
from django.core.exceptions import ValidationError
from libs.maximum_length_validator import MaximumLengthValidator
from libs.zxcvbn_validator import ZxcvbnValidator


class PasswordValidationTests(TestCase):

    def setUp(self):
        self.max_len_validator = MaximumLengthValidator()
        self.complexity_validator = ZxcvbnValidator()

    def test_password_invalid_length(self):
        password_short = "aaa"
        password_too_long = ''.join(["a" * 65])

        # short password OK
        try:
            self.max_len_validator.validate(password_short)
        except Exception:
            self.fail(f"Password validation should succeed when the password is not too long.")

        # too long password NOT OK
        self.assertRaisesRegexp(ValidationError,
                                "This password is too long. It must contain a maximum of 64 characters.",
                                self.max_len_validator.validate,
                                password_too_long)

    def test_password_complexity(self):
        password_not_complex = "abc"
        password_complex = "p@$swr0d44"

        # complex password OK
        try:
            self.complexity_validator.validate(password_complex)
        except Exception:
            self.fail(f"Password validation should succeed when the password is complex enough.")

        # easy-to-guess password NOT OK
        self.assertRaisesRegexp(ValidationError,
                                "This password is not complex enough.*",
                                self.complexity_validator.validate,
                                password_not_complex)
