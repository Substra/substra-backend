import json
import ntpath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework import status

from substrapp.management.commands.bulkcreatedatasample import bulk_create_data_sample, InvalidException
from substrapp.management.utils.localRequest import LocalRequest
from substrapp.serializers import (DataManagerSerializer, LedgerDataManagerSerializer,
                                   LedgerObjectiveSerializer, ObjectiveSerializer)
from substrapp.utils import get_hash
from substrapp.views.datasample import LedgerException


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Command(BaseCommand):
    help = '''  # noqa
    create objective
    python ./manage.py createobjective '{"objective": {"name": "foo", "metrics_name": "accuracy", "metrics": "./metrics.py", "description": "./description.md", "permissions": {"public": True, "authorized_ids": []}}, "data_manager": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "permissions": {"public": True, "authorized_ids": []}, "data_samples": {"paths": ["./data.zip", "./train/data"]}}'
    python ./manage.py createobjective objective.json
    # objective.json:
    # {"objective": {"name": "foo", "metrics_name": "accuracy", "metrics": "./metrics.py", "description": "./description.md", "permissions": {"public": True, "authorized_ids": []}, "data_manager": {"name": "foo", "data_opener": "./opener.py", "description": "./description.md", "type": "foo", "permissions": {"public": True, "authorized_ids": []}, "data_samples": {"paths": ["./data.zip", "./train/data"]}}
    '''

    def add_arguments(self, parser):
        parser.add_argument('data_input', type=str)
        parser.add_argument('channel_name', type=str)

    def handle(self, *args, **options):

        # load args
        args = options['data_input']
        channel_name = options['channel_name']

        try:
            data_input = json.loads(args)
        except Exception:
            try:
                with open(args, 'r') as f:
                    data_input = json.load(f)
            except Exception:
                raise CommandError('Invalid args. Please review help')
        else:
            if not isinstance(data_input, dict):
                raise CommandError(
                    'Invalid args. Please provide a valid json file.')

        # get datamanager and check
        data_manager = data_input.get('data_manager', None)
        if data_manager is None:
            return self.stderr.write('Please provide a data_manager')
        if 'name' not in data_manager:
            return self.stderr.write('Please provide a name to your data_manager')
        if 'type' not in data_manager:
            return self.stderr.write('Please provide a type to your data_manager')
        if 'data_opener' not in data_manager:
            return self.stderr.write(
                'Please provide a data_opener to your data_manager')
        if 'description' not in data_manager:
            return self.stderr.write(
                'Please provide a description to your data_manager')
        if 'permissions' not in data_manager:
            return self.stderr.write(
                'Please provide permissions to your data_manager')

        # get data and check
        data_samples = data_input.get('data_samples', None)
        if data_samples is None:
            return self.stderr.write('Please provide some data_samples')
        if 'paths' not in data_samples:
            return self.stderr.write('Please provide paths to your data_samples')

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
        if 'permissions' not in objective:
            return self.stderr.write(
                'Please provide permissions to your objective')

        # by default data need to be test_only
        data_samples['test_only'] = True

        # TODO add validation
        with open(data_manager['data_opener'], 'rb') as f:
            filename = path_leaf(data_manager['data_opener'])
            data_opener = ContentFile(f.read(), filename)

        with open(data_manager['description'], 'rb') as f:
            filename = path_leaf(data_manager['description'])
            description = ContentFile(f.read(), filename)

        data_manager_pkhash = get_hash(data_opener)
        serializer = DataManagerSerializer(data={
            'pkhash': data_manager_pkhash,
            'data_opener': data_opener,
            'description': description,
            'name': data_manager['name'],
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            self.stderr.write(json.dumps({'message': str(e), 'pkhash': data_manager_pkhash}))
        else:
            # create on db
            try:
                instance = serializer.save()
            except Exception as e:
                self.stderr.write(str(e))
            else:
                # init ledger serializer
                ledger_serializer = LedgerDataManagerSerializer(
                    data={'name': data_manager['name'],
                          'permissions': data_manager['permissions'],
                          'type': data_manager['type'],
                          'instance': instance},
                    context={'request': LocalRequest()})

                try:
                    ledger_serializer.is_valid()
                except Exception as e:
                    # delete instance
                    instance.delete()
                    self.stderr.write(str(e))
                else:
                    # create on ledger
                    res, st = ledger_serializer.create(channel_name, ledger_serializer.validated_data)

                    if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED, status.HTTP_408_REQUEST_TIMEOUT):
                        self.stderr.write(json.dumps(res, indent=2))
                    else:
                        d = dict(serializer.data)
                        d.update(res)
                        msg = f'Successfully added datamanager with status code {st} and result: ' \
                              f'{json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))

        # Try to add data even if datamanager creation failed
        self.stdout.write('Will add data samples to this datamanager now')
        # Add data in bulk now
        data_samples.update({'data_manager_keys': [data_manager_pkhash]})
        data_sample_pkhashes = []
        try:
            res_data, st = bulk_create_data_sample(data_samples)
        except LedgerException as e:
            if e.st == status.HTTP_408_REQUEST_TIMEOUT:
                self.stdout.write(
                    self.style.WARNING(json.dumps(e.data, indent=2)))
            else:
                self.stderr.write(json.dumps(e.data, indent=2))
        except InvalidException as e:
            data_sample_pkhashes = e.data
            self.stderr.write(json.dumps({'message': e.msg, 'pkhash': data_sample_pkhashes}, indent=2))
        except Exception as e:
            self.stderr.write(str(e))
        else:
            msg = f'Successfully bulk added data samples with status code {st} and result: ' \
                  f'{json.dumps(res_data, indent=4)}'
            self.stdout.write(self.style.SUCCESS(msg))
            data_sample_pkhashes = [x['pkhash'] for x in res_data]

        # Try to add objective even if datamanager or data creation failed (409 or others)
        self.stdout.write('Will add objective to this datamanager now')
        # Add data in bulk now
        objective.update({'test_data_manager_key': data_manager_pkhash})
        objective.update({'test_data_sample_keys': data_sample_pkhashes})

        # TODO add validation
        with open(objective['metrics'], 'rb') as f:
            filename = path_leaf(objective['metrics'])
            metrics = ContentFile(f.read(), filename)

        with open(objective['description'], 'rb') as f:
            filename = path_leaf(objective['description'])
            description = ContentFile(f.read(), filename)

        pkhash = get_hash(description)
        serializer = ObjectiveSerializer(data={
            'pkhash': pkhash,
            'metrics': metrics,
            'description': description,
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            self.stderr.write(json.dumps({'message': str(e), 'pkhash': pkhash}))
        else:
            # create on db
            try:
                instance = serializer.save()
            except Exception as e:
                self.stderr.write(str(e))
            else:
                # init ledger serializer
                ledger_serializer = LedgerObjectiveSerializer(
                    data={'name': objective['name'],
                          'permissions': objective['permissions'],
                          'metrics_name': objective['metrics_name'],
                          'test_data_sample_keys': objective.get('test_data_sample_keys', []),
                          'test_data_manager_key': objective.get('test_data_manager_key', ''),
                          'instance': instance},
                    context={'request': LocalRequest()})

                try:
                    ledger_serializer.is_valid()
                except Exception as e:
                    # delete instance
                    instance.delete()
                    self.stderr.write(str(e))
                else:
                    # create on ledger
                    res, st = ledger_serializer.create(
                        channel_name,
                        ledger_serializer.validated_data)

                    if st not in (
                            status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED,
                            status.HTTP_408_REQUEST_TIMEOUT):
                        self.stderr.write(json.dumps(res, indent=2))
                    else:
                        d = dict(serializer.data)
                        d.update(res)
                        msg = f'Successfully added objective with status code {st} and result: ' \
                              f'{json.dumps(res, indent=4)}'
                        self.stdout.write(self.style.SUCCESS(msg))
