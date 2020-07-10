import re
import tempfile

from django.db import IntegrityError
from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from substrapp.models import Objective
from substrapp.serializers import ObjectiveSerializer, LedgerObjectiveSerializer

from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerTimeout, LedgerConflict
from substrapp.utils import get_hash
from substrapp.views.utils import (PermissionMixin, find_primary_key_error, validate_pk,
                                   get_success_create_code, ValidationException,
                                   LedgerException, get_remote_asset, validate_sort,
                                   node_has_process_permission)
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, objective):
    objective['description']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:objective-description', args=[objective['key']]))
    objective['metrics']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:objective-metrics', args=[objective['key']])
    )


class ObjectiveViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    ledger_query_call = 'queryObjective'

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, request):
        # create on local db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as e:
            try:
                pkhash = re.search(r'\(pkhash\)=\((\w+)\)', e.args[0]).group(1)
            except IndexError:
                pkhash = ''
            err_msg = 'A objective with this description file already exists.'
            return {'message': err_msg, 'pkhash': pkhash}, status.HTTP_409_CONFLICT
        except Exception as e:
            raise Exception(e.args)

        # init ledger serializer
        ledger_data = {
            'test_data_sample_keys': request.data.get('test_data_sample_keys') or [],
            'test_data_manager_key': request.data.get('test_data_manager_key', ''),
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
            'metrics_name': request.data.get('metrics_name'),
            'metadata': request.data.get('metadata')
        }
        ledger_data.update({'instance': instance})
        ledger_serializer = LedgerObjectiveSerializer(data=ledger_data,
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

    def _create(self, request):
        metrics = request.data.get('metrics')
        description = request.data.get('description')

        try:
            pkhash = get_hash(description)
        except Exception as e:
            st = status.HTTP_400_BAD_REQUEST
            raise ValidationException(e.args, '(not computed)', st)

        serializer = self.get_serializer(data={
            'pkhash': pkhash,
            'metrics': metrics,
            'description': description,
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

        try:
            data = self._create(request)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def create_or_update_objective(self, objective, pk):
        # get description from remote node
        url = objective['description']['storageAddress']

        content = get_remote_asset(url, objective['owner'], pk)

        # write objective with description in local db for later use
        tmp_description = tempfile.TemporaryFile()
        tmp_description.write(content)
        instance, created = Objective.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', tmp_description)
        return instance

    def _retrieve(self, request, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger('mychannel', pk, self.ledger_query_call)

        # do not cache if node has not process permission
        if node_has_process_permission(data):
            # try to get it from local db to check if description exists
            try:
                instance = self.get_object()
            except Http404:
                instance = None

            if not instance or not instance.description:
                instance = self.create_or_update_objective(data, pk)

            # For security reason, do not give access to local file address
            # Restrain data to some fields
            # TODO: do we need to send creation date and/or last modified date ?
            serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
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
            data = query_ledger('mychannel', fcn='queryObjectives', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        objectives_list = [data]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                objectives_list = filter_list(
                    object_type='objective',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        for group in objectives_list:
            for objective in group:
                replace_storage_addresses(request, objective)

        return Response(objectives_list, status=status.HTTP_200_OK)

    @action(detail=True)
    def data(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO fetch list of data from ledger
        # query list of related algos and models from ledger

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def leaderboard(self, request, pk):
        sort = request.query_params.get('sort', 'desc')

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_sort(sort)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            leaderboard = query_ledger('mychannel', fcn='queryObjectiveLeaderboard', args={
                'objectiveKey': pk,
                'ascendingOrder': sort == 'asc',
            })
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        return Response(leaderboard, status=status.HTTP_200_OK)


class ObjectivePermissionViewSet(PermissionMixin,
                                 GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    ledger_query_call = 'queryObjective'

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path='description', url_name='description')
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, 'description')

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.download_file(request, 'metrics')
