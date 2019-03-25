import json
import ntpath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.management.commands.bulkcreatedata import bulk_create_data
from substrapp.serializers import DataManagerSerializer, LedgerDataManagerSerializer
from substrapp.utils import get_hash
from substrapp.views.data import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''
    create datamanager
    python ./manage.py createdatamanager '{"datamanager": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "objective_keys": [], "permissions": "all"}, "data": {"paths": ["./data.zip", "./train/data"], "test_only": false}}'
    python ./manage.py createdatamanager datamanager.json
    # data.json:
    # objective_keys and permissions are optional
    # {"datamanager": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "objective_keys": [], "permissions": "all"}, "data": {"paths": ["./data.zip", "./train/data"], "test_only": false}}
    '''

    def add_arguments(self, parser):
        parser.add_argument('data_input', type=str)

    def handle(self, *args, **options):

        # load args
        args = options['data_input']
        try:
            data_input = json.loads(args)
        except:
            try:
                with open(args, 'r') as f:
                    data_input = json.load(f)
            except:
                raise CommandError('Invalid args. Please review help')
        else:
            if not isinstance(data_input, dict):
                raise CommandError('Invalid args. Please provide a valid json file.')

        datamanager = data_input.get('datamanager', None)
        if datamanager is None:
            return self.stderr.write('Please provide a datamanager')
        if 'name' not in datamanager:
            return self.stderr.write('Please provide a name to your datamanager')
        if 'type' not in datamanager:
            return self.stderr.write('Please provide a type to your datamanager')
        if 'data_opener' not in datamanager:
            return self.stderr.write('Please provide a data_opener to your datamanager')
        if 'description' not in datamanager:
            return self.stderr.write('Please provide a description to your datamanager')

        data = data_input.get('data', None)
        if data is None:
            return self.stderr.write('Please provide some data')
        if 'paths' not in data:
            return self.stderr.write('Please provide paths to your data')
        if 'test_only' not in data:
            return self.stderr.write('Please provide a boolean test_only parameter to your data')

        # TODO add validation
        with open(datamanager['data_opener'], 'rb') as f:
            filename = path_leaf(datamanager['data_opener'])
            data_opener = ContentFile(f.read(), filename)

        with open(datamanager['description'], 'rb') as f:
            filename = path_leaf(datamanager['description'])
            description = ContentFile(f.read(), filename)

        pkhash = get_hash(data_opener)
        serializer = DataManagerSerializer(data={
            'pkhash': pkhash,
            'data_opener': data_opener,
            'description': description,
            'name': datamanager['name'],
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            self.stderr.write(str(e))
        else:
            # create on db
            try:
                instance = serializer.save()
            except Exception as e:
                self.stderr.write(str(e))
            else:
                # init ledger serializer
                ledger_serializer = LedgerDataManagerSerializer(
                    data={'name': datamanager['name'],
                          'permissions': datamanager.get('permissions', ''),
                          'type': datamanager['type'],
                          'objective_keys': datamanager.get('objective_keys', []),
                          'instance': instance})

                try:
                    ledger_serializer.is_valid()
                except Exception as e:
                    # delete instance
                    instance.delete()
                    self.stderr.write(str(e))
                else:
                    # create on ledger
                    res, st = ledger_serializer.create(
                        ledger_serializer.validated_data)

                    if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED, status.HTTP_408_REQUEST_TIMEOUT):
                        self.stderr.write(json.dumps(res, indent=2))
                    else:
                        d = dict(serializer.data)
                        d.update(res)
                        msg = f'Succesfully added datamanager with status code {st} and result: {json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))

        # Try to add data even if datamanager creation failed

        self.stdout.write('Will add data to this datamanager now')
        # Add data in bulk now
        data.update({'datamanager_keys': [pkhash]})
        try:
            res, st = bulk_create_data(data)
        except LedgerException as e:
            if e.st == status.HTTP_408_REQUEST_TIMEOUT:
                self.stdout.write(self.style.WARNING(json.dumps(e.data, indent=2)))
            else:
                self.stderr.write(json.dumps(e.data, indent=2))
        except Exception as e:
            return self.stderr.write(str(e))
        else:
            msg = f'Succesfully bulk added data with status code {st} and result: {json.dumps(res, indent=4)}'
            self.stdout.write(self.style.SUCCESS(msg))
