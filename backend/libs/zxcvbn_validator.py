from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from zxcvbn import zxcvbn


class ZxcvbnValidator:

    def validate(self, password, user=None):
        results = zxcvbn(password, user_inputs=[user])

        # score to the password, from 0 (terrible) to 4 (great)
        if results['score'] < 3:
            str = 'This password is not complex enough.'
            if results['feedback']['warning']:
                str += f"\nwarning: {results['feedback']['warning']}"
            raise ValidationError(_(str), code='password_not_complex')

    def get_help_text(self):
        return _("Your password must be a complex one")
