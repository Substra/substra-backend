import json
import ntpath
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from substrapp.models import Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer
from substrapp.utils import get_hash


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''
    Bulk create data

    python ./manage.py bulkcreatedata '{"files": ["./data1.zip", "./data2.zip"], "dataset_keys": ["bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af"], "test_only": false}'
    python ./manage.py bulkcreatedata data.json

    # data.json:
    # {"files": ["./data1.zip", "./data2.zip"], "dataset_keys": ["bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af"], "test_only": false}
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

        data_files = data.get('files', None)
        files = {}
        if data_files and type(data_files) == list:
            for file in data_files:
                with open(file, 'rb') as f:
                    filename = path_leaf(file)
                    files[filename] = ContentFile(f.read(), filename)

        dataset_keys = data.get('dataset_keys', [])

        if not type(dataset_keys) == list:
            return self.stderr('The dataset_keys you provided is not an array')

        dataset_count = Dataset.objects.filter(pkhash__in=dataset_keys).count()

        # check all dataset exists
        if not len(dataset_keys) or dataset_count != len(dataset_keys):
            return self.stderr.write(f'One or more dataset keys provided do not exist in local substrabac database. Please create them before. Dataset keys: {dataset_keys}')

        # bulk
        if files:
            l = []
            for x in files:
                file = files[path_leaf(x)]
                l.append({
                    'pkhash': get_hash(file),
                    'file': file
                })

            serializer = DataSerializer(data=l, many=True)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                return self.stderr(str(e))
            else:
                # create on db
                try:
                    instances = serializer.save()
                except IntegrityError as exc:
                    self.stderr.write('One of the Data you passed already exists in the substrabac local database. Please review your args.')
                except Exception as exc:
                    raise Exception(exc.args)
                else:
                    # init ledger serializer

                    ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                                   'dataset_keys': dataset_keys,
                                                                   'instances': instances})

                    if not ledger_serializer.is_valid():
                        # delete instance
                        for instance in instances:
                            instance.delete()
                        raise ValidationError(ledger_serializer.errors)

                    # create on ledger
                    data, st = ledger_serializer.create(ledger_serializer.validated_data)

                    for d in serializer.data:
                        if d['pkhash'] in data['pkhash'] and data['validated'] is not None:
                            d['validated'] = data['validated']

                    self.stdout.write(self.style.SUCCESS(f'Succesfully added data via bulk with status code {st} and data: {json.dumps(serializer.data, indent=4)}'))
