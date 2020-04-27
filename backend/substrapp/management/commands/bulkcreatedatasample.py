import json
import ntpath
import os
from os.path import normpath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.serializers.datasample import DataSampleSerializer
from substrapp.views import DataSampleViewSet
from substrapp.utils import get_archive_hash, get_dir_hash
from substrapp.views.datasample import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class InvalidException(Exception):
    def __init__(self, msg, data):
        self.data = data
        self.msg = msg
        super(LedgerException).__init__()


# check if not already in data sample list
def check(file_or_path, pkhash, data_sample):
    err_msg = 'Your data sample archives/paths contain same files leading to same pkhash, ' \
              'please review the content of your achives/paths. %s and %s are the same'
    for x in data_sample:
        if pkhash == x['pkhash']:
            if 'file' in x:
                p = x['file'].name
            else:
                p = x['path']
            raise Exception(err_msg % (file_or_path, p))


def map_data_sample(paths):
    data_sample = []
    for file_or_path in paths:
        if os.path.exists(file_or_path):

            # file case
            if os.path.isfile(file_or_path):
                with open(file_or_path, 'rb') as f:
                    filename = path_leaf(file_or_path)
                    file = ContentFile(f.read(), filename)
                    pkhash = get_archive_hash(file)

                    check(file_or_path, pkhash, data_sample)

                    data_sample.append({
                        'pkhash': pkhash,
                        'file': file
                    })

            # directory case
            elif os.path.isdir(file_or_path):
                pkhash = get_dir_hash(file_or_path)

                check(file_or_path, pkhash, data_sample)

                data_sample.append({
                    'pkhash': pkhash,
                    'path': normpath(file_or_path)
                })
            else:
                raise Exception(f'{file_or_path} is not a file or a directory')

        else:
            raise Exception(f'File or Path: {file_or_path} does not exist')

    return data_sample


def bulk_create_data_sample(data):
    data_manager_keys = data.get('data_manager_keys', [])
    test_only = data.get('test_only', False)
    paths = data.get('paths', None)

    DataSampleViewSet.check_datamanagers(data_manager_keys)

    if not (paths and type(paths)) == list:
        raise Exception('Please specify a list of paths (can be archives or directories)')

    data_samples = map_data_sample(paths)

    serializer = DataSampleSerializer(data=data_samples, many=True)
    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise InvalidException(msg=str(e), data=[x['pkhash'] for x in data_samples])

    # create on ledger + db
    ledger_data = {'test_only': test_only,
                   'data_manager_keys': data_manager_keys}
    return DataSampleViewSet.commit(serializer, ledger_data)


class Command(BaseCommand):
    help = '''  # noqa
    Bulk create data sample
    paths is a list of archives or paths to directories
    python ./manage.py bulkcreatedatasample '{"paths": ["./data1.zip", "./data2.zip", "./train/data", "./train/data2"], "data_manager_keys": ["9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528"], "test_only": false}'
    python ./manage.py bulkcreatedatasample data.json
    # data.json:
    # {"paths": ["./data1.zip", "./data2.zip", "./train/data", "./train/data2"], "data_manager_keys": ["9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528"], "test_only": false}
    '''

    def add_arguments(self, parser):
        parser.add_argument('data', type=str)

    def handle(self, *args, **options):

        # load args
        args = options['data']
        try:
            data = json.loads(args)
        except Exception:
            try:
                with open(args, 'r') as f:
                    data = json.load(f)
            except Exception:
                raise CommandError('Invalid args. Please review help')
        else:
            if not isinstance(data, dict):
                raise CommandError('Invalid args. Please provide a valid json file.')

        data_manager_keys = data.get('data_manager_keys', [])
        if not type(data_manager_keys) == list:
            return self.stderr.write('The data_manager_keys you provided is not an array')

        try:
            res, st = bulk_create_data_sample(data)
        except LedgerException as e:
            if e.st == status.HTTP_408_REQUEST_TIMEOUT:
                self.stdout.write(self.style.WARNING(json.dumps(e.data, indent=2)))
            else:
                self.stderr.write(json.dumps(e.data, indent=2))
        except InvalidException as e:
            self.stderr.write(e.msg)
        except Exception as e:
            self.stderr.write(str(e))
        else:
            msg = f'Successfully added data samples via bulk with status code {st} and data: ' \
                  f'{json.dumps(res, indent=4)}'
            self.stdout.write(self.style.SUCCESS(msg))
