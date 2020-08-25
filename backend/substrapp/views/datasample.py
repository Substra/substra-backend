import logging
from os.path import normpath

import os
import ntpath
import shutil

from django.conf import settings
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import DataSample, DataManager
from substrapp.serializers import DataSampleSerializer, LedgerDataSampleSerializer, LedgerDataSampleUpdateSerializer
from substrapp.utils import store_datasamples_archive, get_dir_hash
from substrapp.views.utils import find_primary_key_error, LedgerException, ValidationException, \
    get_success_create_code
from substrapp.ledger_utils import query_ledger, LedgerError, LedgerTimeout, LedgerConflict

logger = logging.getLogger(__name__)


class DataSampleViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    queryset = DataSample.objects.all()
    serializer_class = DataSampleSerializer

    @staticmethod
    def check_datamanagers(data_manager_keys):
        datamanager_count = DataManager.objects.filter(pkhash__in=data_manager_keys).count()

        if datamanager_count != len(data_manager_keys):
            raise Exception(f'One or more datamanager keys provided do not exist in local database. '
                            f'Please create them before. DataManager keys: {data_manager_keys}')

    @staticmethod
    def commit(serializer, ledger_data):
        instances = serializer.save()
        # init ledger serializer
        ledger_data.update({'instances': instances})
        ledger_serializer = LedgerDataSampleSerializer(data=ledger_data)

        if not ledger_serializer.is_valid():
            # delete instance
            for instance in instances:
                instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerTimeout as e:
            if isinstance(serializer.data, list):
                pkhash = [x['pkhash'] for x in serializer.data]
            else:
                pkhash = [serializer.data['pkhash']]
            data = {'pkhash': pkhash, 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.pkhash, e.status)
        except LedgerError as e:
            for instance in instances:
                instance.delete()
            raise LedgerException(str(e.msg), e.status)
        except Exception:
            for instance in instances:
                instance.delete()
            raise

        st = get_success_create_code()

        # update validated to True in response
        if 'pkhash' in data and data['validated']:
            for d in serializer.data:
                if d['pkhash'] in data['pkhash']:
                    d.update({'validated': data['validated']})

        return serializer.data, st

    def compute_data(self, request, paths_to_remove):

        data = {}

        # files can be uploaded inside the HTTP request or can already be
        # available on local disk
        if len(request.FILES) > 0:
            pkhash_map = {}

            for k, file in request.FILES.items():
                # Get dir hash uncompress the file into a directory
                pkhash, datasamples_path_from_file = store_datasamples_archive(file)  # can raise
                paths_to_remove.append(datasamples_path_from_file)
                # check pkhash does not belong to the list
                try:
                    data[pkhash]
                except KeyError:
                    pkhash_map[pkhash] = file
                else:
                    raise Exception(f'Your data sample archives contain same files leading to same pkhash, '
                                    f'please review the content of your achives. '
                                    f'Archives {file} and {pkhash_map[pkhash]} are the same')
                data[pkhash] = {
                    'pkhash': pkhash,
                    'path': datasamples_path_from_file
                }

        else:  # files must be available on local filesystem
            path = request.data.get('path')
            paths = request.data.get('paths') or []

            if path and paths:
                raise Exception('Cannot use path and paths together.')
            if path is not None:
                paths = [path]

            recursive_dir_field = BooleanField()
            recursive_dir = recursive_dir_field.to_internal_value(request.data.get('multiple', 'false'))
            if recursive_dir:
                # list all directories from parent directories
                parent_paths = paths
                paths = []
                for parent_path in parent_paths:
                    subdirs = next(os.walk(parent_path))[1]
                    subdirs = [os.path.join(parent_path, s) for s in subdirs]
                    if not subdirs:
                        raise Exception(
                            f'No data sample directories in folder {parent_path}')
                    paths.extend(subdirs)

            # paths, should be directories
            for path in paths:
                if not os.path.isdir(path):
                    raise Exception(f'One of your paths does not exist, '
                                    f'is not a directory or is not an absolute path: {path}')
                pkhash = get_dir_hash(path)
                try:
                    data[pkhash]
                except KeyError:
                    pass
                else:
                    # existing can be a dict with a field path or file
                    raise Exception(f'Your data sample directory contain same files leading to same pkhash. '
                                    f'Invalid path: {path}.')

                data[pkhash] = {
                    'pkhash': pkhash,
                    'path': normpath(path)
                }

        if not data:
            raise Exception('No data sample provided.')

        return list(data.values())

    def _create(self, request, data_manager_keys, test_only):

        # compute_data will uncompress data archives to paths which will be
        # hardlinked thanks to datasample pre_save signal.
        # In all other cases, we need to remove those references.

        if not data_manager_keys:
            raise Exception("missing or empty field 'data_manager_keys'")

        self.check_datamanagers(data_manager_keys)  # can raise

        paths_to_remove = []

        try:
            # will uncompress data archives to paths
            computed_data = self.compute_data(request, paths_to_remove)

            serializer = self.get_serializer(data=computed_data, many=True)

            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                pkhashes = [x['pkhash'] for x in computed_data]
                st = status.HTTP_400_BAD_REQUEST
                if find_primary_key_error(e):
                    st = status.HTTP_409_CONFLICT
                raise ValidationException(e.args, pkhashes, st)
            else:

                # create on ledger + db
                ledger_data = {'test_only': test_only,
                               'data_manager_keys': data_manager_keys}
                data, st = self.commit(serializer, ledger_data)  # pre_save signal executed
                return data, st
        finally:
            for gpath in paths_to_remove:
                shutil.rmtree(gpath, ignore_errors=True)

    def create(self, request, *args, **kwargs):
        test_only = request.data.get('test_only', False)
        data_manager_keys = request.data.get('data_manager_keys') or []

        try:
            data, st = self._create(request, data_manager_keys, test_only)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryDataSamples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data if data else []

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def bulk_update(self, request):
        ledger_serializer = LedgerDataSampleUpdateSerializer(data=dict(request.data))
        ledger_serializer.is_valid(raise_exception=True)

        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            st = status.HTTP_200_OK
        else:
            st = status.HTTP_202_ACCEPTED
        return Response(data, status=st)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)
