import tempfile

from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from substrapp.models import Objective
from substrapp.serializers import ObjectiveSerializer, LedgerObjectiveSerializer

from substrapp.ledger.api import query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError, LedgerTimeout, LedgerConflict
from substrapp.utils import get_hash
from substrapp.views.utils import (PermissionMixin, validate_pk,
                                   get_success_create_code, ValidationException,
                                   LedgerException, get_remote_asset, validate_sort,
                                   node_has_process_permission, get_channel_name,
                                   data_to_data_response)
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, objective):
    objective['description']['storage_address'] = request.build_absolute_uri(
        reverse('substrapp:objective-description', args=[objective['key']]))
    objective['metrics']['storage_address'] = request.build_absolute_uri(
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
            data = ledger_serializer.create(get_channel_name(request), ledger_serializer.validated_data)
        except LedgerTimeout as e:
            raise LedgerException('timeout', e.status)
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.status)
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
            checksum = get_hash(description)
        except Exception as e:
            raise ValidationException(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={
            'metrics': metrics,
            'description': description,
            'checksum': checksum
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationException(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)
        else:
            # create on ledger + db
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):

        try:
            data = self._create(request)
        except ValidationException as e:
            return Response({'message': e.data}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            # Transform data to a data_response with only key
            data_response = data_to_data_response(data)
            return Response(data_response, status=st, headers=headers)

    def create_or_update_objective(self, channel_name, objective, pk):
        # get description from remote node
        url = objective['description']['storage_address']
        hash = objective['description']['hash']

        content = get_remote_asset(channel_name, url, objective['owner'], hash)

        # write objective with description in local db for later use
        tmp_description = tempfile.TemporaryFile()
        tmp_description.write(content)
        instance, created = Objective.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', tmp_description)
        return instance

    def _retrieve(self, request, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger(get_channel_name(request), pk, self.ledger_query_call)

        # do not cache if node has not process permission
        if node_has_process_permission(data):
            # try to get it from local db to check if description exists
            try:
                instance = self.get_object()
            except Http404:
                instance = None

            if not instance or not instance.description:
                instance = self.create_or_update_objective(get_channel_name(request), data, pk)

            # For security reason, do not give access to local file address
            # Restrain data to some fields
            # TODO: do we need to send creation date and/or last modified date ?
            serializer = self.get_serializer(instance, fields=('owner'))
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
            data = query_ledger(get_channel_name(request), fcn='queryObjectives', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                data = filter_list(
                    channel_name=get_channel_name(request),
                    object_type='objective',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        for objective in data:
            replace_storage_addresses(request, objective)

        return Response(data, status=status.HTTP_200_OK)

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
            leaderboard = query_ledger(get_channel_name(request), fcn='queryObjectiveLeaderboard', args={
                'objective_key': pk,
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
