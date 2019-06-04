import ast
import tempfile
import logging
from django.conf import settings
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.models import DataManager
from substrapp.serializers import DataManagerSerializer, LedgerDataManagerSerializer
from substrapp.serializers.ledger.datamanager.util import updateLedgerDataManager
from substrapp.serializers.ledger.datamanager.tasks import updateLedgerDataManagerAsync
from substrapp.utils import get_hash, JsonException, get_from_node
from substrapp.ledger_utils import query_ledger, get_object_from_ledger
from substrapp.views.utils import (ManageFileMixin, ComputeHashMixin, find_primary_key_error,
                                   validate_pk)
from substrapp.views.filters_utils import filter_list


class DataManagerViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         ComputeHashMixin,
                         ManageFileMixin,
                         GenericViewSet):
    queryset = DataManager.objects.all()
    serializer_class = DataManagerSerializer
    ledger_query_call = 'queryDataManager'

    def perform_create(self, serializer):
        return serializer.save()

    def dryrun(self, data_opener):

        file = data_opener.open().read()

        try:
            node = ast.parse(file)
        except BaseException:
            return Response({
                'message': f'Opener must be a valid python file, please review your opener file and the documentation.'
            }, status=status.HTTP_400_BAD_REQUEST)

        imported_module_names = [m.name for e in node.body if isinstance(e, ast.Import) for m in e.names]
        if 'substratools' not in imported_module_names:
            return Response({
                'message': 'Opener must import substratools, please review your opener and the documentation.'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f'Your data opener is valid. You can remove the dryrun option.'
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        dryrun = request.data.get('dryrun', False)
        data_opener = request.data.get('data_opener')

        pkhash = get_hash(data_opener)
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
            return Response({'message': e.args, 'pkhash': pkhash}, status=st)

        if dryrun:
            return self.dryrun(data_opener)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except Exception as e:
            return Response({'message': e.args},
                            status=status.HTTP_400_BAD_REQUEST)

        # init ledger serializer
        ledger_serializer = LedgerDataManagerSerializer(data={
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
            'type': request.data.get('type'),
            'objective_keys': request.data.getlist('objective_keys'),
            'instance': instance
        }, context={'request': request})

        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        data, st = ledger_serializer.create(ledger_serializer.validated_data)
        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED, status.HTTP_408_REQUEST_TIMEOUT):
            return Response(data, status=st)

        headers = self.get_success_headers(serializer.data)
        d = dict(serializer.data)
        d.update(data)
        return Response(d, status=st, headers=headers)

    def create_or_update_datamanager(self, instance, datamanager, pk):

        # create instance if does not exist
        if not instance:
            instance, created = DataManager.objects.update_or_create(
                pkhash=pk, name=datamanager['name'], validated=True)

        if not instance.data_opener:
            url = datamanager['opener']['storageAddress']

            response = get_from_node(url)

            try:
                computed_hash = self.compute_hash(response.content)
            except Exception as e:
                raise Exception('Failed to fetch opener file') from e

            if computed_hash != pk:
                msg = 'computed hash is not the same as the hosted file. ' \
                      'Please investigate for default of synchronization, corruption, or hacked'
                raise Exception(msg)

            f = tempfile.TemporaryFile()
            f.write(response.content)

            # save/update data_opener in local db for later use
            instance.data_opener.save('opener.py', f)

        # do the same for description
        if not instance.description:
            url = datamanager['description']['storageAddress']

            response = get_from_node(url)

            try:
                computed_hash = self.compute_hash(response.content)
            except Exception as e:
                raise Exception('Failed to fetch description file') from e

            if computed_hash != datamanager['description']['hash']:
                msg = 'computed hash is not the same as the hosted file. ' \
                      'Please investigate for default of synchronization, corruption, or hacked'
                raise Exception(msg)

            f = tempfile.TemporaryFile()
            f.write(response.content)

            # save/update description in local db for later use
            instance.description.save('description.md', f)

        return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)

        # get instance from remote node
        try:
            data = get_object_from_ledger(pk, 'queryDataset')
        except JsonException as e:
            return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response(f'No element with key {pk}', status=status.HTTP_404_NOT_FOUND)

        # try to get it from local db to check if description exists
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        # check if instance has description or data_opener
        if not instance or not instance.description or not instance.data_opener:
            try:
                instance = self.create_or_update_datamanager(instance, data, pk)
            except Exception as e:
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # do not give access to local files address
        serializer = self.get_serializer(
            instance,
            fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
        data.update(serializer.data)

        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):

        data, st = query_ledger(fcn='queryDataManagers', args=[])
        data = data if data else []

        data_managers_list = [data]

        if st == status.HTTP_200_OK:

            # parse filters
            query_params = request.query_params.get('search', None)

            if query_params is not None:
                try:
                    data_managers_list = filter_list(
                        object_type='dataset',
                        data=data,
                        query_params=query_params)
                except Exception as e:
                    logging.exception(e)
                    return Response(
                        {'message': f'Malformed search filters {query_params}'},
                        status=status.HTTP_400_BAD_REQUEST)

        return Response(data_managers_list, status=st)

    @action(methods=['post'], detail=True)
    def update_ledger(self, request, *args, **kwargs):

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)

        objective_key = request.data.get('objective_key')
        args = [pk, objective_key]

        if getattr(settings, 'LEDGER_SYNC_ENABLED'):
            data, st = updateLedgerDataManager(args, sync=True)
            # patch status for update
            if st == status.HTTP_201_CREATED:
                st = status.HTTP_200_OK
            return Response(data, status=st)

        else:
            # use a celery task, as we are in an http request transaction
            updateLedgerDataManagerAsync.delay(args)
            data = {
                'message': 'The substra network has been notified for updating this DataManager'
            }
            st = status.HTTP_202_ACCEPTED
            return Response(data, status=st)

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.manage_file('data_opener')
