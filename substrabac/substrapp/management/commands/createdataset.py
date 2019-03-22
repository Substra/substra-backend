import json
import ntpath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.management.commands.bulkcreatedata import bulk_create_data
from substrapp.models import Dataset
from substrapp.serializers import DatasetSerializer, LedgerDatasetSerializer
from substrapp.utils import get_hash
from substrapp.views.data import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''
    create dataset
    python ./manage.py createdataset '{"dataset": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "challenge_keys": [], "permissions": "all"}, "data": {"paths": ["./data.zip", "./train/data"], "test_only": false}}'
    python ./manage.py createdataset dataset.json
    # data.json:
    # challenge_keys and permissions are optional
    # {"dataset": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "challenge_keys": [], "permissions": "all"}, "data": {"paths": ["./data.zip", "./train/data"], "test_only": false}}
    '''

    def add_arguments(self, parser):
        parser.add_argument('data', type=str)

    def handle(self, *args, **options):

        # load args
        args = options['data']
        try:
            data = json.loads(args)
        except:
            try:
                with open(args, 'r') as f:
                    data = json.load(f)
            except:
                raise CommandError('Invalid args. Please review help')
        else:
            if not isinstance(data, dict):
                raise CommandError('Invalid args. Please provide a valid json file.')

        dataset = data.get('dataset', None)
        if dataset is None:
            return self.stderr.write('Please provide a dataset')
        if 'name' not in dataset:
            return self.stderr.write('Please provide a name to your dataset')
        if 'type' not in dataset:
            return self.stderr.write('Please provide a type to your dataset')
        if 'data_opener' not in dataset:
            return self.stderr.write('Please provide a data_opener to your dataset')
        if 'description' not in dataset:
            return self.stderr.write('Please provide a description to your dataset')

        data = data.get('data', None)
        if data is None:
            return self.stderr.write('Please provide some data')
        if 'paths' not in data:
            return self.stderr.write('Please provide paths to your data')
        if 'test_only' not in data:
            return self.stderr.write('Please provide test_only parameter to your data')

        # TODO add validation
        with open(dataset['data_opener'], 'rb') as f:
            filename = path_leaf(dataset['data_opener'])
            data_opener = ContentFile(f.read(), filename)

        with open(dataset['description'], 'rb') as f:
            filename = path_leaf(dataset['description'])
            description = ContentFile(f.read(), filename)

        pkhash = get_hash(data_opener)
        serializer = DatasetSerializer(data={
            'pkhash': pkhash,
            'data_opener': data_opener,
            'description': description,
            'name': dataset['name'],
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
                ledger_serializer = LedgerDatasetSerializer(
                    data={'name': dataset['name'],
                          'permissions': data.get('permissions', ''),
                          'type': dataset['type'],
                          'challenge_keys': dataset.get('challenge_keys', []),
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
                        msg = f'Succesfully added dataset with status code {st} and result: {json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))

        # Try to add data even if dataset creation failed

        self.stdout.write('Will add data to this dataset now')
        # Add data in bulk now
        data.update({'dataset_keys': [pkhash]})
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
