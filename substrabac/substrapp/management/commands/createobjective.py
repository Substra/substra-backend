import json
import ntpath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.management.commands.bulkcreatedata import bulk_create_data
from substrapp.serializers import DatasetSerializer, LedgerDatasetSerializer, \
    ChallengeSerializer, LedgerChallengeSerializer
from substrapp.serializers.ledger.dataset.util import updateLedgerDataset
from substrapp.utils import get_hash
from substrapp.views.data import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''
    create dataset
    python ./manage.py createobjective '{"objective": {"name": "foo", "metrics_name": "accuracy", "metrics": "./metrics.py", "description": "./description.md"}, "dataset": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo"}, "data": {"paths": ["./data.zip", "./train/data"]}}'
    python ./manage.py createobjective objective.json
    # objective.json:
    # permissions are optional
    # {"objective": {"name": "foo", "metrics_name": "accuracy", "metrics": "./metrics.py", "description": "./description.md"}, "dataset": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo"}, "data": {"paths": ["./data.zip", "./train/data"]}}
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
                raise CommandError(
                    'Invalid args. Please provide a valid json file.')

        # get dataset and check
        dataset = data_input.get('dataset', None)
        if dataset is None:
            return self.stderr.write('Please provide a dataset')
        if 'name' not in dataset:
            return self.stderr.write('Please provide a name to your dataset')
        if 'type' not in dataset:
            return self.stderr.write('Please provide a type to your dataset')
        if 'data_opener' not in dataset:
            return self.stderr.write(
                'Please provide a data_opener to your dataset')
        if 'description' not in dataset:
            return self.stderr.write(
                'Please provide a description to your dataset')

        # get data and check
        data = data_input.get('data', None)
        if data is None:
            return self.stderr.write('Please provide some data')
        if 'paths' not in data:
            return self.stderr.write('Please provide paths to your data')

        # get objective and check
        objective = data_input.get('objective', None)
        if objective is None:
            return self.stderr.write('Please provide an objective')
        if 'name' not in objective:
            return self.stderr.write('Please provide a name to your objective')
        if 'metrics_name' not in objective:
            return self.stderr.write(
                'Please provide a metrics_name to your objective')
        if 'metrics' not in objective:
            return self.stderr.write(
                'Please provide a metrics file to your objective')
        if 'description' not in objective:
            return self.stderr.write(
                'Please provide a description to your objective')

        # by default data need to be test_only
        data['test_only'] = True

        # TODO add validation
        with open(dataset['data_opener'], 'rb') as f:
            filename = path_leaf(dataset['data_opener'])
            data_opener = ContentFile(f.read(), filename)

        with open(dataset['description'], 'rb') as f:
            filename = path_leaf(dataset['description'])
            description = ContentFile(f.read(), filename)

        dataset_pkhash = get_hash(data_opener)
        serializer = DatasetSerializer(data={
            'pkhash': dataset_pkhash,
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
                          'permissions': 'all',
                          # forced, TODO changed when permissions are available
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

                    if st not in (
                    status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED,
                    status.HTTP_408_REQUEST_TIMEOUT):
                        self.stderr.write(json.dumps(res, indent=2))
                    else:
                        d = dict(serializer.data)
                        d.update(res)
                        msg = f'Successfully added dataset with status code {st} and result: {json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))

        # Try to add data even if dataset creation failed
        self.stdout.write('Will add data to this dataset now')
        # Add data in bulk now
        data.update({'dataset_keys': [dataset_pkhash]})
        res_data = []
        try:
            res_data, st = bulk_create_data(data)
        except LedgerException as e:
            if e.st == status.HTTP_408_REQUEST_TIMEOUT:
                self.stdout.write(
                    self.style.WARNING(json.dumps(e.data, indent=2)))
            else:
                self.stderr.write(json.dumps(e.data, indent=2))
        except Exception as e:
            return self.stderr.write(str(e))
        else:
            msg = f'Successfully bulk added data with status code {st} and result: {json.dumps(res_data, indent=4)}'
            self.stdout.write(self.style.SUCCESS(msg))

        # Try to add objective even if dataset or data creation failed (409 or others)
        self.stdout.write('Will add objective to this dataset now')
        # Add data in bulk now
        objective.update({'test_dataset_key': dataset_pkhash})
        objective.update({'test_data_keys': res_data})

        # TODO add validation
        with open(objective['metrics'], 'rb') as f:
            filename = path_leaf(objective['metrics'])
            metrics = ContentFile(f.read(), filename)

        with open(objective['description'], 'rb') as f:
            filename = path_leaf(objective['description'])
            description = ContentFile(f.read(), filename)

        pkhash = get_hash(description)
        serializer = ChallengeSerializer(data={
            'pkhash': pkhash,
            'metrics': metrics,
            'description': description,
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
                ledger_serializer = LedgerChallengeSerializer(
                    data={'name': objective['name'],
                          'permissions': 'all',
                          # forced, TODO changed when permissions are available
                          'metrics_name': objective['metrics_name'],
                          'test_data_keys': objective.get('test_data_keys',
                                                          []),
                          'test_dataset_key': objective.get('test_dataset_key',
                                                            ''),
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

                    if st not in (
                            status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED,
                            status.HTTP_408_REQUEST_TIMEOUT):
                        self.stderr.write(json.dumps(res, indent=2))
                    else:
                        d = dict(serializer.data)
                        d.update(res)
                        msg = f'Successfully added objective with status code {st} and result: {json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))

                        # Try to update dataset with this challenge key if success
                        # TODO refacto with updateLedger view
                        self.stdout.write('Will update dataset with this objective now')
                        args = '"%(datasetKey)s", "%(challengeKey)s"' % {
                            'datasetKey': dataset_pkhash,
                            'challengeKey': res['pkhash'],
                        }
                        res, st = updateLedgerDataset(args, sync=True)

                        msg = f'Successfully updated dataset with status code {st} and result: {json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))
