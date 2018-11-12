import json
import ntpath
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from substrapp.models import Dataset
from substrapp.serializers import DataSerializer, LedgerDataSerializer


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''
    Bulk create data
    
    python ./manage.py bulkcreatedata '{"files": ["./data1.zip", "./data2.zip"], "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0", "test_only": false}'
    python ./manage.py bulkcreatedata data.json
    
    # data.json:
    # {"files": ["./data1.zip", "./data2.zip"], "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0", "test_only": false}
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

        try:
            dataset = Dataset.objects.get(pkhash=data.get('dataset_key'))
        except:
            self.stderr.write('This Dataset key: %s does not exist in local substrabac database.' % data.get('dataset_key'))
        else:
            # bulk
            if files:
                serializer = DataSerializer(data=[{'file': files[x]} for x in files], many=True)
                serializer.is_valid(raise_exception=True)
                # create on db
                try:
                    instances = serializer.save()
                except IntegrityError as exc:
                    self.stderr.write('One of the Data you passed already exists in the substrabac local database. Please review your args.')
                except Exception as exc:
                    raise Exception(exc.args)
                else:
                    # init ledger serializer
                    file_size = 0
                    for file in data_files:
                        file_size += os.path.getsize(file)

                    ledger_serializer = LedgerDataSerializer(data={'test_only': data.get('test_only'),
                                                                   'size': file_size,
                                                                   'dataset_key': dataset.pk,
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

                    self.stdout.write(self.style.SUCCESS('Succesfully added data via bulk with status code %s and data: %s') % (st, json.dumps(serializer.data, indent=4)))
