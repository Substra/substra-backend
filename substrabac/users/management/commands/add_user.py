import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Add user'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password', nargs='?', default=secrets.token_hex(8))

    def handle(self, *args, **options):
        try:
            User.objects.create_user(username=options['username'], password=options['password'])
        except IntegrityError as e:
            self.stderr.write(f'User already exists: {str(e)}')
        else:
            self.stdout.write(f"password: {options['password']}")
