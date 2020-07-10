import tempfile
from django.conf import settings
from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp import ledger
from substrapp.models import DataManager
from substrapp.serializers import DataManagerSerializer, LedgerDataManagerSerializer
from substrapp.utils import get_hash
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerTimeout, LedgerConflict
from substrapp.views.utils import (PermissionMixin, find_primary_key_error,
                                   validate_pk, get_success_create_code, ValidationException, LedgerException,
                                   get_remote_asset, node_has_process_permission)
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, data_manager):
    data_manager['description']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:data_manager-description', args=[data_manager['key']]))
    data_manager['opener']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:data_manager-opener', args=[data_manager['key']])
    )


class DataManagerViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer
    ledger_query_call = 'queryDataManager'

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, request):
        # create on ledger + db
        ledger_data = {
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
            'type': request.data.get('type'),
            'objective_key': request.data.get('objective_key', ''),
            'metadata': request.data.get('metadata')
        }

        # create on db
        instance = self.perform_create(serializer)
        # init ledger serializer
        ledger_data.update({'instance': instance})
        ledger_serializer = LedgerDataManagerSerializer(data=ledger_data,
                                                        context={'request': request})

        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create('mychannel', ledger_serializer.validated_data)
        except LedgerTimeout as e:
            data = {'pkhash': [x['pkhash'] for x in serializer.data], 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.pkhash, e.status)
        except LedgerError as e:
            instance.delete()
            raise LedgerException(str(e.msg), e.status)
        except Exception:
            instance.delete()
            raise

        d = dict(serializer.data)
        d.update(data)

        return d

    def _create(self, request, data_opener):

        try:
            pkhash = get_hash(data_opener)
        except Exception as e:
            st = status.HTTP_400_BAD_REQUEST
            raise ValidationException(e.args, '(not computed)', st)

        serializer = self.get_serializer(data={
            'pkhash': pkhash,
            'data_opener': data_opener,
            'description': request.data.get('description'),
            'name': request.data.get('name'),
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            st = status.HTTP_400_BAD_REQUEST
            if find_primary_key_error(e):
                st = status.HTTP_409_CONFLICT
            raise ValidationException(e.args, pkhash, st)
        else:
            # create on ledger + db
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):
        data_opener = request.data.get('data_opener')

        try:
            data = self._create(request, data_opener)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def create_or_update_datamanager(self, instance, datamanager, pk):

        # create instance if does not exist
        if not instance:
            instance, created = DataManager.objects.update_or_create(
                pkhash=pk, name=datamanager['name'], validated=True)

        if not instance.data_opener:
            url = datamanager['opener']['storageAddress']

            content = get_remote_asset(url, datamanager['owner'], datamanager['opener']['hash'])

            f = tempfile.TemporaryFile()
            f.write(content)

            # save/update data_opener in local db for later use
            instance.data_opener.save('opener.py', f)

        # do the same for description
        if not instance.description:
            url = datamanager['description']['storageAddress']

            content = get_remote_asset(url, datamanager['owner'], datamanager['description']['hash'])

            f = tempfile.TemporaryFile()
            f.write(content)

            # save/update description in local db for later use
            instance.description.save('description.md', f)

        return instance

    def _retrieve(self, request, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger('mychannel', pk, 'queryDataset')

        # do not cache if node has not process permission
        if node_has_process_permission(data):
            # try to get it from local db to check if description exists
            try:
                instance = self.get_object()
            except Http404:
                instance = None
            finally:
                # check if instance has description or data_opener
                if not instance or not instance.description or not instance.data_opener:
                    instance = self.create_or_update_datamanager(instance, data, pk)

                # do not give access to local files address
                serializer = self.get_serializer(instance, fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
                data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):

        try:
            data = query_ledger('mychannel', fcn='queryDataManagers', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data_managers_list = [data]

        # parse filters
        query_params = request.query_params.get('search', None)

        if query_params is not None:
            try:
                data_managers_list = filter_list(
                    object_type='dataset',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        for group in data_managers_list:
            for data_manager in group:
                replace_storage_addresses(request, data_manager)

        return Response(data_managers_list, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def update_ledger(self, request, *args, **kwargs):

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        objective_key = request.data.get('objective_key')
        args = {
            'dataManagerKey': pk,
            'objectiveKey': objective_key,
        }

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            st = status.HTTP_200_OK
        else:
            st = status.HTTP_202_ACCEPTED

        try:
            data = ledger.update_datamanager('mychannel', args)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        return Response(data, status=st)


class DataManagerPermissionViewSet(PermissionMixin,
                                   GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer
    ledger_query_call = 'queryDataManager'

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path='description', url_name='description')
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, 'description')

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.download_file(request, 'data_opener', 'opener')
