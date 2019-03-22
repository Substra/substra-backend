import json
import ntpath
import os
from os.path import normpath

from checksumdir import dirhash
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.serializers.data import DataSerializer
from substrapp.views import DataViewSet
from substrapp.utils import get_dir_hash
from substrapp.views.data import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


# check if not already in data list
def check(file_or_path, pkhash, data):
    err_msg = f'Your data archives/paths contain same files leading to same pkhash, please review the content of your achives/paths. %s and %s are the same'
    for x in data:
        if pkhash == x['pkhash']:
            if 'file' in x:
                p = x['file'].name
            else:
                p = x['path']
            raise Exception(err_msg % (file_or_path, p))


def map_data(paths):
    data = []
    for file_or_path in paths:
        if os.path.exists(file_or_path):

            # file case
            if os.path.isfile(file_or_path):
                with open(file_or_path, 'rb') as f:
                    filename = path_leaf(file_or_path)
                    file = ContentFile(f.read(), filename)
                    pkhash = get_dir_hash(file)

                    check(file_or_path, pkhash, data)

                    data.append({
                        'pkhash': pkhash,
                        'file': file
                    })

            # directory case
            elif os.path.isdir(file_or_path):
                pkhash = dirhash(file_or_path, 'sha256')

                check(file_or_path, pkhash, data)

                data.append({
                    'pkhash': pkhash,
                    'path': normpath(file_or_path)
                })
            else:
                raise Exception(f'{file_or_path} is not a file or a directory')

        else:
            raise Exception(f'File or Path: {file_or_path} does not exist')

    return data


def bulk_create_data(data):
    dataset_keys = data.get('dataset_keys', [])
    test_only = data.get('test_only', False)
    paths = data.get('paths', None)

    DataViewSet.check_datasets(dataset_keys)

    if not (paths and type(paths)) == list:
        raise Exception('Please specify a list of paths (can be archives or directories)')

    data = map_data(paths)

    serializer = DataSerializer(data=data, many=True)
    serializer.is_valid(raise_exception=True)

    # create on ledger + db
    ledger_data = {'test_only': test_only,
                   'dataset_keys': dataset_keys}
    return DataViewSet.commit(serializer, ledger_data, True)


class Command(BaseCommand):
    help = '''
    Bulk create data
    file_paths is a list of archives or paths
    python ./manage.py bulkcreatedata '{"paths": ["./data1.zip", "./data2.zip", "./train/data", "./train/data2"], "dataset_keys": ["bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af"], "test_only": false}'    
    python ./manage.py bulkcreatedata data.json
    # data.json:
    # {"paths": ["./data1.zip", "./data2.zip", "./train/data", "./train/data2"], "dataset_keys": ["bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af"], "test_only": false}
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

        dataset_keys = data.get('dataset_keys', [])
        if not type(dataset_keys) == list:
            return self.stderr.write('The dataset_keys you provided is not an array')

        try:
            res, st = bulk_create_data(data)
        except LedgerException as e:
            if e.st == status.HTTP_408_REQUEST_TIMEOUT:
                self.stdout.write(self.style.WARNING(json.dumps(e.data, indent=2)))
            else:
                self.stderr.write(json.dumps(e.data, indent=2))
        except Exception as e:
            self.stderr.write(str(e))
        else:
            msg = f'Succesfully added data via bulk with status code {st} and data: {json.dumps(res, indent=4)}'
            self.stdout.write(self.style.SUCCESS(msg))
