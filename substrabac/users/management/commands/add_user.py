import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Add user'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password', nargs='?', default=secrets.token_hex(8))

    def handle(self, *args, **options):

        username = options['username']
        password = options['password']

        try:
            validate_password(password, self.UserModel(username=username))
        except ValidationError as err:
            self.stderr.write('\n'.join(err.messages))
        else:
            try:
                self.UserModel.objects.create_user(username=username, password=password)
            except IntegrityError as e:
                self.stderr.write(f'User already exists: {str(e)}')
            else:
                self.stdout.write(f"password: {password}")
